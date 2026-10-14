from pathlib import Path

import pandas as pd

DATA_DIR = Path("/home/ec2-user/studies/Haochen_food/code_micro/data")
RELATIONSHIP_DIR = DATA_DIR / "train_relationship"
FDR = 0.05


def genus_of(species):
    name = str(species)
    if "g__" in name and "_s__" in name:
        return name.split("g__")[-1].split("_s__")[0]
    return name.split("s__")[-1].split("_")[0]


def main():
    keys = ["diet_pattern", "outcome"]
    primary = pd.read_csv(RELATIONSHIP_DIR / "diet_pattern_species_primary_model.csv")[keys + ["beta", "fdr_q"]]
    extended = pd.read_csv(RELATIONSHIP_DIR / "diet_pattern_species_extended_model.csv")[keys + ["beta", "fdr_q"]]
    both = primary.merge(extended, on=keys, suffixes=("_primary", "_extended"), validate="one_to_one")

    sig_primary = both["fdr_q_primary"] < FDR
    sig_both = sig_primary & (both["fdr_q_extended"] < FDR)
    concordant = (both["beta_primary"] > 0) == (both["beta_extended"] > 0)
    out_dir = RELATIONSHIP_DIR / "pattern_profiles"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame({
        "metric": ["tests", "significant_primary", "significant_both_models", "significant_both_discordant"],
        "value": [len(both), int(sig_primary.sum()), int(sig_both.sum()), int((sig_both & ~concordant).sum())],
    })
    summary.to_csv(out_dir / "association_summary.csv", index=False)

    sig = both.loc[sig_both]
    counts = sig.groupby("diet_pattern")["beta_primary"].agg(
        n_associations="size", n_positive=lambda b: int((b > 0).sum()), n_negative=lambda b: int((b < 0).sum()))
    counts.to_csv(out_dir / "associations_per_pattern.csv")

    profiles = primary.pivot(index="outcome", columns="diet_pattern", values="beta")
    profiles.corr(method="spearman").to_csv(out_dir / "pattern_profile_spearman.csv")

    groups = sig.assign(genus=sig["outcome"].map(genus_of)).groupby(["diet_pattern", "genus"])["beta_primary"].agg(
        n_species="size", opposing=lambda b: bool((b > 0).any() and (b < 0).any())).reset_index()
    groups = groups[groups["n_species"] >= 2]
    groups.to_csv(out_dir / "within_genus_directions.csv", index=False)

    print(summary.to_string(index=False))
    print(counts.to_string())
    print(f"Pattern-genus groups with >=2 associated species: {len(groups)}; "
          f"opposing directions: {int(groups['opposing'].sum())}")


if __name__ == "__main__":
    main()
