import argparse
import concurrent.futures
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import false_discovery_control, pearsonr, t
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler

from abundance_preprocessing import PREVALENCE_MIN_COUNT, genus_detection_count, validate_preprocessing

DATA_DIR = Path(os.environ.get("NHANES_DATA_DIR", "data")) / "processed"
COVARIATES = ["age", "sex", "bmi", "smoking_binary", "oralhealth_gum_disease", "oralhealth_teeth_mobility_lately"]
DIET_FEATURES = [
    "Energy", "diet_event_count_mean", "Foods_per_day", "Categories_per_day", "Meals_per_day", "Foods_per_meal",
    "Eating_window_hours", "nutrient_daily_mean_carbohydrate_g", "nutrient_daily_mean_total_fat_g",
    "nutrient_daily_mean_protein_g", "nutrient_daily_mean_fiber_g", "nutrient_daily_mean_sodium_mg",
    "nutrient_daily_mean_alcohol_g", "nutrient_per_1000kcal_fiber_g", "nutrient_per_1000kcal_sodium_mg",
    "pct_carb_calories", "pct_protein_calories", "pct_fat_calories", "pct_alcohol_calories", "low_carb_diet",
]
N_PERMUTATIONS = 500
PERMUTATION_SEED = 2907
FDR = 0.05
STRATEGIES = {"species_to_genus": "species-to-genus strategy", "direct_genus": "direct genus-level strategy"}


def build_lgbm():
    import lightgbm as lgb

    return lgb.LGBMRegressor(
        objective="regression", max_depth=4, n_estimators=2000, subsample=0.5, subsample_freq=1,
        colsample_bytree=0.3, learning_rate=0.001, random_state=1, reg_alpha=1, reg_lambda=1,
        min_data_in_leaf=20, n_jobs=1, verbosity=-1,
    )


def preprocess_x_fold(x_train, x_test):
    x_train = x_train.astype(float).copy()
    x_test = x_test.astype(float).copy()
    medians = x_train.median()
    x_train, x_test = x_train.fillna(medians), x_test.fillna(medians)
    binary = [c for c in x_train.columns if set(x_train[c].unique()).issubset({0.0, 1.0})]
    continuous = [c for c in x_train.columns if c not in binary]
    if continuous:
        scaler = StandardScaler()
        x_train.loc[:, continuous] = scaler.fit_transform(x_train[continuous])
        x_test.loc[:, continuous] = scaler.transform(x_test[continuous])
    return x_train, x_test


def oof_pearson(x, y):
    prediction = np.full(len(y), np.nan)
    for train, test in KFold(n_splits=5, shuffle=False).split(x):
        x_train, x_test = preprocess_x_fold(x.iloc[train], x.iloc[test])
        scaler = StandardScaler()
        model = build_lgbm()
        model.fit(x_train, scaler.fit_transform(y[train, None]).ravel())
        prediction[test] = scaler.inverse_transform(model.predict(x_test)[:, None]).ravel()
    r, p = pearsonr(y, prediction)
    return float(r), float(p)


def ols_association(frame, feature, target):
    x = np.column_stack([np.ones(len(frame)), frame[feature]] + [frame[c] for c in COVARIATES]).astype(float)
    y = frame[target].to_numpy(dtype=float)
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    residual = y - x @ beta
    df = len(y) - x.shape[1]
    se = np.sqrt((residual @ residual) / df * np.linalg.pinv(x.T @ x)[1, 1])
    return float(beta[1]), float(2 * t.sf(abs(beta[1] / se), df))


def bh(p):
    return false_discovery_control(np.asarray(p, dtype=float), method="bh")


def load_cohort(path):
    frame = pd.read_parquet(path).sort_values("SEQN").reset_index(drop=True)
    validate_preprocessing(frame)
    assert frame[COVARIATES].notna().all().all()
    return frame


def exact_genus_columns(pipeline):
    taxonomy = pd.read_parquet(DATA_DIR / f"oral_microbiome_dada2{pipeline}_taxonomy_annotation.parquet")
    names = taxonomy.set_index("Name")["Taxonomy in SILVA v123"].astype(str).str.split(";").str[-1]
    return names.groupby(names).size()


def within_cycle_permutations(frame):
    rng = np.random.default_rng(PERMUTATION_SEED)
    groups = list(frame.groupby("cycle", sort=True).indices.values())
    indices = []
    for _ in range(N_PERMUTATIONS):
        index = np.arange(len(frame))
        for group in groups:
            index[group] = rng.permutation(group)
        indices.append(index)
    return np.asarray(indices)


def eligibility(args):
    candidates = json.loads(Path(args.hpp_genera).read_text())
    frame = load_cohort(args.cohort)
    rb, rsv = exact_genus_columns("rb"), exact_genus_columns("rsv")
    rows, evaluable = [], {}
    for strategy in STRATEGIES:
        evaluable[strategy] = []
        for genus in candidates[strategy]:
            matched = rb.get(genus, 0) == 1 and rsv.get(genus, 0) == 1
            column = "genus_log10__" + genus
            detected = genus_detection_count(frame, genus) if matched else 0
            variance = float(frame[column].var()) if matched and column in frame else 0.0
            ok = matched and column in frame and (
                strategy != "direct_genus" or (detected >= PREVALENCE_MIN_COUNT and variance > 0))
            rows.append({"strategy": strategy, "genus": genus, "exact_match_both_versions": matched,
                         "detected_n": detected, "log10_variance": variance, "evaluable": ok})
            if ok:
                evaluable[strategy].append(genus)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "genus_eligibility.csv", index=False)
    (out / "evaluable_genera.json").write_text(json.dumps(evaluable, indent=2) + "\n")
    print({k: len(v) for k, v in evaluable.items()})


def _genus_task(task):
    frame, genus, features, index = task
    data = frame.copy()
    if index is not None:
        data[DIET_FEATURES] = frame[DIET_FEATURES].to_numpy()[index]
    return oof_pearson(data[features], data["genus_log10__" + genus].to_numpy(dtype=float))[0]


def genus_replication(args):
    frame = load_cohort(args.cohort)
    evaluable = json.loads((Path(args.out_dir) / "evaluable_genera.json").read_text())
    genera = list(dict.fromkeys(evaluable["species_to_genus"] + evaluable["direct_genus"]))
    observed = {}
    for genus in genera:
        y = frame["genus_log10__" + genus].to_numpy(dtype=float)
        observed[genus] = {"covariates": oof_pearson(frame[COVARIATES], y),
                           "covariates_plus_diet": oof_pearson(frame[COVARIATES + DIET_FEATURES], y)}
    indices = within_cycle_permutations(frame)
    tasks = [(frame, g, COVARIATES + DIET_FEATURES, indices[i]) for i in range(N_PERMUTATIONS) for g in genera]
    with concurrent.futures.ProcessPoolExecutor(args.workers) as pool:
        null_r = list(pool.map(_genus_task, tasks, chunksize=4))
    null = pd.DataFrame([(i, g) for i in range(N_PERMUTATIONS) for g in genera], columns=["permutation", "genus"])
    null["null_r"] = null_r
    null["null_delta_r"] = null["null_r"] - null["genus"].map({g: v["covariates"][0] for g, v in observed.items()})

    out = Path(args.out_dir)
    summary = {}
    for strategy, label in STRATEGIES.items():
        rows = []
        for genus in evaluable[strategy]:
            r0, _ = observed[genus]["covariates"]
            r1, p1 = observed[genus]["covariates_plus_diet"]
            delta = r1 - r0
            null_delta = null.loc[null["genus"].eq(genus), "null_delta_r"].to_numpy()
            rows.append({"genus": genus, "r_covariates": r0, "r_covariates_plus_diet": r1, "p_covariates_plus_diet": p1,
                         "delta_r": delta, "increment_p": (1 + (null_delta >= delta).sum()) / (N_PERMUTATIONS + 1)})
        table = pd.DataFrame(rows)
        table["q_covariates_plus_diet"] = bh(table["p_covariates_plus_diet"])
        table["increment_q"] = bh(table["increment_p"])
        table["replicated"] = table["q_covariates_plus_diet"].lt(FDR) & table["delta_r"].gt(0) & table["increment_q"].lt(FDR)
        table.to_csv(out / f"genus_replication_{strategy}.csv", index=False)
        summary[strategy] = {"replicated": int(table["replicated"].sum()), "evaluable": len(table)}
    null.to_csv(out / "genus_increment_null.csv", index=False)
    (out / "genus_replication_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(summary)


def _pairwise_task(task):
    frame, genus, feature = task
    return oof_pearson(frame[COVARIATES + [feature]], frame["genus_log10__" + genus].to_numpy(dtype=float))[0]


def pairwise_replication(args):
    frame = load_cohort(args.cohort)
    genera = json.loads((Path(args.out_dir) / "evaluable_genera.json").read_text())["direct_genus"]
    hpp = pd.read_csv(args.hpp_pairs)
    pairs = [(g, f) for g in genera for f in DIET_FEATURES]
    with concurrent.futures.ProcessPoolExecutor(args.workers) as pool:
        single = list(pool.map(_pairwise_task, [(frame, g, f) for g, f in pairs], chunksize=2))
    baseline = {g: oof_pearson(frame[COVARIATES], frame["genus_log10__" + g].to_numpy(dtype=float))[0] for g in genera}
    rows = []
    for (genus, feature), r_single in zip(pairs, single):
        beta, p = ols_association(frame, feature, "genus_log10__" + genus)
        rows.append({"genus": genus, "diet_feature": feature, "nhanes_beta": beta, "nhanes_p": p,
                     "r_covariates": baseline[genus], "r_covariates_plus_feature": r_single,
                     "delta_r": r_single - baseline[genus]})
    table = pd.DataFrame(rows)
    table["nhanes_q"] = bh(table["nhanes_p"])
    table = table.merge(hpp, on=["genus", "diet_feature"], how="left", validate="one_to_one")
    table["concordant_direction"] = np.sign(table["nhanes_beta"]) == np.sign(table["hpp_beta"])
    table["replicated"] = (table["hpp_candidate"].astype(bool) & table["nhanes_q"].lt(FDR)
                           & table["delta_r"].gt(0) & table["concordant_direction"])
    out = Path(args.out_dir)
    table.to_csv(out / "pairwise_replication.csv", index=False)
    summary = {"pairs_tested": len(table), "hpp_candidates": int(table["hpp_candidate"].astype(bool).sum()),
               "replicated_within_candidates": int(table["replicated"].sum())}
    (out / "pairwise_replication_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=["eligibility", "genus", "pairwise"])
    parser.add_argument("--cohort", default="outputs/nhanes_analysis_cohort.parquet")
    parser.add_argument("--hpp-genera", help="JSON with HPP candidate genera: 'species_to_genus', 'direct_genus'")
    parser.add_argument("--hpp-pairs", help="CSV of HPP diet-genus results: genus, diet_feature, hpp_beta, hpp_candidate")
    parser.add_argument("--out-dir", default="outputs/nhanes_replication")
    parser.add_argument("--workers", type=int, default=os.cpu_count())
    args = parser.parse_args()
    {"eligibility": eligibility, "genus": genus_replication, "pairwise": pairwise_replication}[args.step](args)


if __name__ == "__main__":
    main()
