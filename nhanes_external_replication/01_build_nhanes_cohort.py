import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from abundance_preprocessing import PREPROCESSING_COLUMN, PREPROCESSING_ID, preprocess_abundances

DATA_DIR = Path(os.environ.get("NHANES_DATA_DIR", "data")) / "processed"
NUTRIENTS = {"energy_kcal": "KCAL", "carbohydrate_g": "CARB", "total_fat_g": "TFAT", "protein_g": "PROT",
             "fiber_g": "FIBE", "sodium_mg": "SODI", "alcohol_g": "ALCO"}
FPED_TOP_LEVEL = ["F_TOTAL", "V_TOTAL", "G_TOTAL", "PF_TOTAL", "D_TOTAL", "OILS", "SOLID_FATS", "ADD_SUGARS", "A_DRINKS"]
DIET_FEATURES = [
    "Energy", "diet_event_count_mean", "Foods_per_day", "Categories_per_day", "Meals_per_day", "Foods_per_meal",
    "Eating_window_hours", "nutrient_daily_mean_carbohydrate_g", "nutrient_daily_mean_total_fat_g",
    "nutrient_daily_mean_protein_g", "nutrient_daily_mean_fiber_g", "nutrient_daily_mean_sodium_mg",
    "nutrient_daily_mean_alcohol_g", "nutrient_per_1000kcal_fiber_g", "nutrient_per_1000kcal_sodium_mg",
    "pct_carb_calories", "pct_protein_calories", "pct_fat_calories", "pct_alcohol_calories", "low_carb_diet",
]
COVARIATES = ["age", "sex", "bmi", "smoking_binary", "oralhealth_gum_disease", "oralhealth_teeth_mobility_lately"]


def valid_recall_days():
    totals = pd.read_parquet(DATA_DIR / "diet_totals_day1_day2.parquet")
    days = []
    for day in (1, 2):
        p = f"DR{day}"
        sub = totals.loc[totals["diet_day"].eq(day)]
        energy = pd.to_numeric(sub[p + "TKCAL"], errors="coerce")
        energy = energy.mask(energy.abs() < 1e-10, 0)
        keep = sub[p + "DRSTZ"].eq(1) & energy.gt(0)
        d = sub.loc[keep, ["SEQN", "cycle", "diet_day"]].copy()
        for name, suffix in NUTRIENTS.items():
            value = pd.to_numeric(sub.loc[keep, p + "T" + suffix], errors="coerce")
            d[name] = value.mask(value.abs() < 1e-10, 0)
        days.append(d)
    return pd.concat(days, ignore_index=True)


def daily_features(days):
    foods = pd.read_parquet(DATA_DIR / "diet_day1_day2.parquet", columns=["SEQN", "diet_day", "food_code", "DR1_020", "DR2_020"])
    foods = foods.merge(days[["SEQN", "diet_day"]], on=["SEQN", "diet_day"], how="inner", validate="many_to_one")
    seconds = pd.to_numeric(np.where(foods["diet_day"].eq(1), foods["DR1_020"], foods["DR2_020"]), errors="coerce")
    foods["seconds"] = pd.Series(seconds, index=foods.index).where(lambda s: s.between(0, 86399))
    foods["hour"] = np.floor(foods["seconds"] / 3600)
    behaviour = foods.groupby(["SEQN", "diet_day"]).agg(
        diet_event_count_mean=("food_code", "size"),
        Foods_per_day=("food_code", "nunique"),
        Meals_per_day=("hour", "nunique"),
        first=("seconds", "min"),
        last=("seconds", "max"),
    ).reset_index()
    behaviour["Foods_per_meal"] = behaviour["Foods_per_day"] / behaviour["Meals_per_day"].replace(0, np.nan)
    behaviour["Eating_window_hours"] = (behaviour["last"] - behaviour["first"]) / 3600
    behaviour = behaviour.drop(columns=["first", "last"])

    fped = pd.read_parquet(DATA_DIR / "fped_day1_day2.parquet")
    categories = []
    for day in (1, 2):
        sub = fped.loc[fped["diet_day"].eq(day)]
        d = sub[["SEQN", "diet_day"]].copy()
        d["Categories_per_day"] = sub[[f"DR{day}T_{c}" for c in FPED_TOP_LEVEL]].gt(0).sum(axis=1)
        categories.append(d)
    categories = pd.concat(categories, ignore_index=True)

    daily = (days.merge(behaviour, on=["SEQN", "diet_day"], how="left", validate="one_to_one")
                 .merge(categories, on=["SEQN", "diet_day"], how="left", validate="one_to_one"))
    daily["Energy"] = daily["energy_kcal"]
    for name in NUTRIENTS:
        if name != "energy_kcal":
            daily["nutrient_daily_mean_" + name] = daily[name]
    for name in ("fiber_g", "sodium_mg"):
        daily["nutrient_per_1000kcal_" + name] = daily[name] / daily["energy_kcal"] * 1000
    for name, factor, label in [("carbohydrate_g", 4, "carb"), ("protein_g", 4, "protein"),
                                ("total_fat_g", 9, "fat"), ("alcohol_g", 7, "alcohol")]:
        daily[f"pct_{label}_calories"] = daily[name] * factor / daily["energy_kcal"] * 100
    daily["low_carb_diet"] = daily["pct_carb_calories"].between(10, 26).astype(float)
    return daily


def covariates():
    p = pd.read_parquet(DATA_DIR / "nhanes_2009_2012_participants.parquet")
    cov = pd.DataFrame({"SEQN": p["SEQN"], "age": p["RIDAGEYR"], "sex": p["RIAGENDR"].map({1: 1.0, 2: 0.0}), "bmi": p["BMXBMI"]})
    smoking = pd.Series(np.nan, index=p.index)
    smoking.loc[p["SMQ020"].eq(2)] = 0.0
    smoking.loc[p["SMQ020"].eq(1) & p["SMQ040"].isin([1, 2])] = 1.0
    smoking.loc[p["SMQ020"].eq(1) & p["SMQ040"].eq(3)] = 0.0
    cov["smoking_binary"] = smoking
    cov["oralhealth_gum_disease"] = p["OHQ835"].map({1: 1.0, 2: 0.0})
    cov["oralhealth_teeth_mobility_lately"] = p["OHQ855"].map({1: 1.0, 2: 0.0})
    return cov


def genus_log10(genera, profile, taxonomy):
    names = taxonomy.set_index("Name")["Taxonomy in SILVA v123"]
    columns = [c for c in profile.columns if c.startswith("RB_genus")]
    raw = profile[columns].apply(pd.to_numeric, errors="raise")
    # The normalization denominator includes all prevalence-retained genera,
    # independently of the HPP candidate lists.
    log10, detected, summary = preprocess_abundances(raw)
    summary.insert(1, "genus", [str(names.get(c, "")).split(";")[-1] for c in columns])
    out = pd.DataFrame({"SEQN": profile["SEQN"].to_numpy()})
    out[PREPROCESSING_COLUMN] = PREPROCESSING_ID
    for genus in genera:
        match = [c for c in columns if str(names.get(c, "")).split(";")[-1] == genus]
        if len(match) != 1:
            print(f"{genus}: no single exact SILVA genus match in DADA2RB ({len(match)}); not evaluable")
            continue
        column = match[0]
        out["genus_detected__" + genus] = detected[column].to_numpy()
        if column not in log10:
            print(f"{genus}: detected in fewer than 200 analysis participants; not retained")
            continue
        out["genus_log10__" + genus] = log10[column].to_numpy()
    return out, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--genera", required=True, help="JSON file with 'species_to_genus' and 'direct_genus' lists")
    parser.add_argument("--out", default="outputs/nhanes_analysis_cohort.parquet")
    args = parser.parse_args()
    lists = json.loads(Path(args.genera).read_text())
    genera = list(dict.fromkeys(lists["species_to_genus"] + lists["direct_genus"]))

    days = valid_recall_days()
    daily = daily_features(days)
    diet = daily.groupby("SEQN")[DIET_FEATURES].mean().reset_index()
    cycle = days.drop_duplicates("SEQN").set_index("SEQN")["cycle"]
    diet["cycle"] = diet["SEQN"].map(cycle)
    diet["diet_recall_days"] = days.groupby("SEQN")["diet_day"].nunique().reindex(diet["SEQN"]).to_numpy()

    profile = pd.read_parquet(DATA_DIR / "oral_microbiome_dada2rb_genus_relative.parquet")
    taxonomy = pd.read_parquet(DATA_DIR / "oral_microbiome_dada2rb_taxonomy_annotation.parquet")
    columns = [c for c in profile.columns if c.startswith("RB_genus")]
    raw = profile[columns].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(raw.to_numpy()).all() or raw.lt(0).any().any():
        raise ValueError("Genus abundances must be finite and non-negative.")
    matched = diet.merge(covariates(), on="SEQN", how="inner", validate="one_to_one").merge(
        profile.loc[raw.gt(0).any(axis=1), ["SEQN"]], on="SEQN", how="inner", validate="one_to_one")

    in_age = matched["age"].between(30, 69)
    cohort = matched[in_age].dropna(subset=COVARIATES)
    cohort = cohort.sort_values("SEQN").reset_index(drop=True)
    cohort_profile = profile.set_index("SEQN").loc[cohort["SEQN"]].reset_index()
    transformed, prevalence = genus_log10(genera, cohort_profile, taxonomy)
    cohort = cohort.merge(transformed, on="SEQN", how="inner", validate="one_to_one")
    flow = {
        "participants_with_reliable_recalls": int(diet["SEQN"].nunique()),
        "matched_diet_microbiome_covariates": int(len(matched)),
        "excluded_age_outside_30_69": int((~in_age).sum()),
        "excluded_incomplete_six_covariates": int(in_age.sum() - len(cohort)),
        "analysis_cohort": int(len(cohort)),
        "by_cycle": cohort["cycle"].value_counts().sort_index().to_dict(),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cohort.to_parquet(out, index=False)
    prevalence.to_csv(out.with_name("nhanes_genus_prevalence.csv"), index=False)
    out.with_name("nhanes_cohort_flow.json").write_text(json.dumps(flow, indent=2) + "\n")
    print(json.dumps(flow, indent=2))


if __name__ == "__main__":
    main()
