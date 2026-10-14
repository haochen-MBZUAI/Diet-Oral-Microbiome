import numpy as np
import pandas as pd

PREVALENCE_MIN_COUNT = 200
PREPROCESSING_COLUMN = "genus_abundance_preprocessing"
PREPROCESSING_ID = "hpp_prevalence200_p01_half_ppm_log10_v1"


def preprocess_abundances(raw):
    """Apply the HPP abundance transformation to the final NHANES cohort."""
    raw = raw.astype(float)
    if not np.isfinite(raw.to_numpy()).all() or raw.lt(0).any().any():
        raise ValueError("Genus abundances must be finite and non-negative.")
    detected = raw.gt(0)
    counts = detected.sum()
    retained = counts[counts >= PREVALENCE_MIN_COUNT].index
    if len(retained) == 0:
        raise ValueError("No genera were detected in at least 200 analysis participants.")

    values = raw.loc[:, retained].copy()
    replacements = {}
    for column in retained:
        replacement = 0.5 * np.percentile(raw.loc[detected[column], column], 1)
        replacements[column] = replacement
        values.loc[~detected[column], column] = replacement
    log10 = np.log10(values.div(values.sum(axis=1), axis=0) * 1e6)
    summary = pd.DataFrame({
        "feature": raw.columns,
        "detected_n": counts.to_numpy(),
        "kept_for_modeling": counts.ge(PREVALENCE_MIN_COUNT).to_numpy(),
        "zero_replacement": [replacements.get(column, np.nan) for column in raw.columns],
    })
    return log10, detected, summary


def genus_detection_count(frame, genus):
    """Count detections recorded before replacement, normalization and log10."""
    column = "genus_detected__" + genus
    if column not in frame:
        raise ValueError("Raw detection indicators are missing; rebuild the NHANES cohort with 01_build_nhanes_cohort.py.")
    detected = frame[column]
    if detected.isna().any() or not detected.isin([False, True]).all():
        raise ValueError(f"{column} must contain non-missing boolean detection indicators.")
    return int(detected.sum())


def validate_preprocessing(frame):
    if PREPROCESSING_COLUMN not in frame or not frame[PREPROCESSING_COLUMN].eq(PREPROCESSING_ID).all():
        raise ValueError("This cohort uses an older abundance transformation; rebuild it with 01_build_nhanes_cohort.py.")
