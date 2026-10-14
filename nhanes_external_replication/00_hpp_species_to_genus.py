import argparse
import json
from pathlib import Path

import pandas as pd


def genus_of(species):
    name = str(species)
    return name.split("g__")[-1].split("_s__")[0] if "g__" in name else name.split("s__")[-1].split("_")[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--species-permutation", required=True)
    parser.add_argument("--out", default="outputs/hpp_genus_candidates.json")
    args = parser.parse_args()

    results = pd.read_csv(args.species_permutation)
    significant = results.loc[results["perm_q_value"] < 0.05, "species"]
    genera = sorted(set(significant.map(genus_of)))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    candidates = json.loads(out.read_text()) if out.exists() else {}
    candidates["species_to_genus"] = genera
    out.write_text(json.dumps(candidates, indent=2) + "\n")
    print(f"{len(significant)} significant species -> {len(genera)} candidate genera")


if __name__ == "__main__":
    main()
