import argparse
import csv
import re
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

SUGAR_SUBSTITUTES = re.compile(
    r"sweetener|stevia|aspartame|sucralose|saccharin|xylitol|erythritol|monk\s*fruit|splenda|"
    r"acesulfame|neotame|advantame|cyclamate|sugar[\s-]*free|zero[\s-]*cal",
    re.IGNORECASE,
)
INCORRECT_FOODS = {"Poppy seed cake", "Salep"}
NUMERIC_COLUMNS = ["participant_id", "logging_day", "weight_g", "calories_kcal", "carbohydrate_g",
                   "lipid_g", "protein_g", "sodium_mg", "alcohol_g", "dietary_fiber_g"]


def text(df, col):
    return df[col].fillna("").astype(str).str.strip() if col in df else pd.Series("", index=df.index)


def number(df, col, default=np.nan):
    return pd.to_numeric(df[col], errors="coerce") if col in df else pd.Series(default, index=df.index)


def read_diet_events(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        row_lengths = Counter(len(row) for row in reader)
    modal_length = row_lengths.most_common(1)[0][0]
    if len(header) == modal_length + 1 and header[:4] == ["participant_id", "id", "cohort", "research_stage"]:
        header.pop(1)
    elif len(header) != modal_length:
        raise ValueError(f"Header has {len(header)} columns but rows have {modal_length}")
    with open(path, encoding="utf-8-sig", newline="") as f, tempfile.NamedTemporaryFile(
            "w", suffix=".csv", newline="", delete=False) as tmp:
        reader = csv.reader(f)
        next(reader)
        writer = csv.writer(tmp)
        writer.writerow(header)
        writer.writerows(row for row in reader if len(row) == len(header))
    df = pd.read_csv(tmp.name, low_memory=False)
    Path(tmp.name).unlink()
    for col in NUMERIC_COLUMNS:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["food_id"] = df["food_id"].astype(str).str.strip()
    return df


def nutrition_ok(df, sweet):
    c, l, p = number(df, "carbohydrate_g"), number(df, "lipid_g"), number(df, "protein_g")
    k, w = number(df, "calories_kcal"), number(df, "weight_g")
    a, f = number(df, "alcohol_g", 0).fillna(0), number(df, "dietary_fiber_g", 0).fillna(0)
    incomplete = c.isna() | l.isna() | p.isna()
    negative = (c < 0) | (l < 0) | (p < 0) | (k < 0) | (w < 0) | (a < 0) | (f < 0)
    mass = c.fillna(0) + l.fillna(0) + p.fillna(0) + a.fillna(0)
    kcal_from_macros = 4 * c.fillna(0) + 9 * l.fillna(0) + 4 * p.fillna(0) + 7 * a.fillna(0)
    incorrect = (
        negative | (p > w) | (l > w * 1.02) | (c > w * 1.15) | (f > w) | (a > w) | (mass > w * 1.10)
        | ((w <= 0) & ((k > 0) | (mass > 0))) | ((k == 0) & (mass > 0))
        | (~sweet & (k >= 30) & ((kcal_from_macros - k).abs() > np.maximum(80, 0.40 * k)))
    )
    return (~incomplete & ~incorrect & ~sweet) | (~negative & sweet)


def clean_diet_events(df):
    steps = {"raw": len(df)}
    date = pd.to_datetime(df["collection_date"], errors="coerce")
    timestamp = pd.to_datetime(df["collection_timestamp"], errors="coerce")
    missing_date = date.isna() & timestamp.notna()
    if missing_date.any():
        df.loc[missing_date, "collection_date"] = timestamp[missing_date].dt.date.astype(str)

    named = (text(df, "short_food_name").str.lower().replace({"nan": "", "none": ""}) != "") | \
            (text(df, "product_name").str.lower().replace({"nan": "", "none": ""}) != "")
    df = df[named & number(df, "calories_kcal").notna()].copy()
    steps["food name and energy"] = len(df)

    min_participants = max(1, int(np.ceil(0.01 * df["participant_id"].nunique())))
    food_participants = df.groupby("food_id")["participant_id"].nunique()
    df = df[df["food_id"].isin(food_participants[food_participants >= min_participants].index)].copy()
    steps["foods recorded by >=1% of participants"] = len(df)

    short, product = text(df, "short_food_name"), text(df, "product_name")
    incorrect_food = short.isin(INCORRECT_FOODS) | short.str.contains("tasters", case=False) | \
        product.str.contains("tasters", case=False) | (short.eq("Halva") & number(df, "lipid_g").fillna(0).eq(0))
    df = df[~incorrect_food].copy()
    sweet = (text(df, "food_category") + " " + text(df, "short_food_name") + " " + text(df, "product_name")) \
        .str.contains(SUGAR_SUBSTITUTES, regex=True)
    df = df[nutrition_ok(df, sweet)].copy()
    steps["nutrient information"] = len(df)

    df = df[number(df, "calories_kcal").between(0, 3000) & number(df, "weight_g").between(0, 2400)].copy()
    steps["energy 0-3,000 kcal and weight 0-2,400 g"] = len(df)

    df["_day"] = pd.to_datetime(df["collection_date"], errors="coerce").dt.normalize()
    df = df[df["_day"].notna()].copy()
    df["_minute"] = pd.to_datetime(df["collection_timestamp"], errors="coerce").dt.floor("min")
    df = df.drop_duplicates(subset=["participant_id", "_day", "_minute", "food_id", "weight_g"])
    steps["duplicates"] = len(df)

    daily = df.groupby(["participant_id", "_day"], as_index=False)["calories_kcal"].sum()
    daily = daily[daily["calories_kcal"].between(500, 4000)]
    stats = daily.groupby("participant_id")["calories_kcal"].agg(["mean", "std", "size"])
    daily = daily.join(stats, on="participant_id")
    low = (daily["size"] >= 2) & (daily["std"] > 0) & (daily["calories_kcal"] < daily["mean"] - 2.5 * daily["std"])
    df = df.merge(daily.loc[~low, ["participant_id", "_day"]], on=["participant_id", "_day"])
    steps["recording days"] = len(df)

    days = df.groupby("participant_id")["_day"].nunique()
    df = df[df["participant_id"].isin(days[days >= 3].index)]
    steps["participants with >=3 recording days"] = len(df)
    return df.drop(columns=["_day", "_minute"]), steps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    output = Path(args.output) if args.output else Path(args.input_csv).with_name("diet_logging_events_cleaned_baseline.csv")
    records = read_diet_events(args.input_csv)
    cleaned, steps = clean_diet_events(records[records["research_stage"] == "00_00_visit"].copy())
    cleaned.to_csv(output, index=False)
    for step, n in steps.items():
        print(f"{step}: {n} rows")
    print("Saved:", output)


if __name__ == "__main__":
    main()
