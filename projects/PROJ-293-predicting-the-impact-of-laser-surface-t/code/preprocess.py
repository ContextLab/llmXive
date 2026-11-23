"""
Preprocess step for the laser surface texturing wear resistance pipeline.

This script implements the three core functions required for Task T003:
1. handle_missing_values
2. archard_normalization
3. split_dataset

It reads the merged dataset produced by the ingestion step
(`data/intermediate/merged.csv`) and writes the following artifacts:

  - data/processed/aggregated_dropped.csv
  - data/processed/aggregated_clean.csv
  - data/processed/normalized_only.csv
  - data/processed/raw_only.csv
  - data/processed/split_summary.json
  - data/processed/train_split.csv
  - data/processed/test_split.csv

The script is designed to be invoked via the main entry point:

    python -m code.main preprocess

It uses a fixed random seed (42) for reproducibility and logs progress
through the project's standard logger obtained via `llmxive_toolkit.get_logger`.
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

from llmxive_toolkit import paths, get_logger
from config.loader import load_schema_map

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
MERGED_CSV_PATH = paths.data("intermediate", "merged.csv")
DROPPED_CSV_PATH = paths.data("processed", "aggregated_dropped.csv")
CLEAN_CSV_PATH = paths.data("processed", "aggregated_clean.csv")
NORMALIZED_CSV_PATH = paths.data("processed", "normalized_only.csv")
RAW_CSV_PATH = paths.data("processed", "raw_only.csv")
SPLIT_SUMMARY_PATH = paths.data("processed", "split_summary.json")
TRAIN_SPLIT_PATH = paths.data("processed", "train_split.csv")
TEST_SPLIT_PATH = paths.data("processed", "test_split.csv")

# Required predictor columns (must be present, otherwise the row is dropped)
REQUIRED_PREDICTORS = [
    "pulse_duration",
    "power",
    "scanning_speed",
    "pattern_geometry",
    "hardness",
    "elastic_modulus",
]

# Columns needed for Archard normalization (optional – if missing, row stays raw)
ARCHARD_LOAD_COL = "contact_load"
ARCHARD_SPEED_COL = "sliding_speed"
# The target wear column – may be linear wear (mm) or mass (mg) – we treat it as a numeric value.
WEAR_RATE_COL = "wear_rate"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_merged() -> pd.DataFrame:
    """Load the merged CSV produced by the ingestion step."""
    if not MERGED_CSV_PATH.exists():
        raise FileNotFoundError(f"Merged dataset not found at {MERGED_CSV_PATH}")
    df = pd.read_csv(MERGED_CSV_PATH)
    return df

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows missing any of the required predictor columns.

    Records with missing `contact_load` or `sliding_speed` are retained
    (they will be flagged as raw later). The function returns a new
    DataFrame with the dropped rows removed and writes the intermediate
    result to `aggregated_dropped.csv`.
    """
    logger = get_logger(__name__)
    logger.info("Handling missing predictor values...")

    # Determine which required predictors are present in the dataframe.
    present_predictors = [col for col in REQUIRED_PREDICTORS if col in df.columns]

    # If none of the required predictors exist, we cannot proceed.
    if not present_predictors:
        raise RuntimeError(
            "None of the required predictor columns are present in the dataset."
        )

    # Count rows before dropping
    before_count = len(df)

    # Drop rows where any present required predictor is NaN
    df_dropped = df.dropna(subset=present_predictors)

    after_count = len(df_dropped)
    dropped = before_count - after_count
    logger.info(f"Dropped {dropped} rows due to missing required predictors.")

    # Write intermediate CSV
    DROPPED_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_dropped.to_csv(DROPPED_CSV_PATH, index=False)
    logger.info(f"Aggregated (dropped) dataset written to {DROPPED_CSV_PATH}")

    return df_dropped

def archard_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Archard's law normalization.

    For rows where both `contact_load` and `sliding_speed` are present,
    we compute a wear coefficient K using a simple formulation:

        K = wear_rate / (contact_load * sliding_speed)

    The result is stored in a new column `wear_coefficient_K` and the
    column `normalization_method` is set to `'normalized'`. Rows lacking
    either of the two required columns retain the original `wear_rate`
    and are marked with `normalization_method='raw'`.

    The cleaned dataframe is written to `aggregated_clean.csv`.
    """
    logger = get_logger(__name__)
    logger.info("Applying Archard normalization...")

    df = df.copy()

    # Ensure required columns exist; if not, create them with NaN so logic works.
    for col in [ARCHARD_LOAD_COL, ARCHARD_SPEED_COL, WEAR_RATE_COL]:
        if col not in df.columns:
            df[col] = pd.NA

    # Determine rows that have both load and speed defined
    has_load = df[ARCHARD_LOAD_COL].notna()
    has_speed = df[ARCHARD_SPEED_COL].notna()
    can_normalize = has_load & has_speed

    # Compute K where possible; avoid division by zero
    def compute_k(row):
        try:
            load = float(row[ARCHARD_LOAD_COL])
            speed = float(row[ARCHARD_SPEED_COL])
            wear = float(row[WEAR_RATE_COL])
            if load == 0 or speed == 0:
                return pd.NA
            return wear / (load * speed)
        except Exception:
            return pd.NA

    df.loc[can_normalize, "wear_coefficient_K"] = df[can_normalize].apply(compute_k, axis=1)

    # Set normalization method flag
    df["normalization_method"] = "raw"
    df.loc[can_normalize, "normalization_method"] = "normalized"

    # Write cleaned CSV
    CLEAN_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_CSV_PATH, index=False)
    logger.info(f"Aggregated (clean) dataset written to {CLEAN_CSV_PATH}")

    return df

def split_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Split the dataset into normalized / raw subsets and then perform a
    stratified 20% held‑out test split (using `source_id` if available,
    otherwise falling back to `normalization_method`). Writes all artefacts
    to disk and returns a summary dictionary.
    """
    logger = get_logger(__name__)
    logger.info("Splitting dataset into training / test splits...")

    # Separate normalized and raw records
    normalized_df = df[df["normalization_method"] == "normalized"].reset_index(drop=True)
    raw_df = df[df["normalization_method"] == "raw"].reset_index(drop=True)

    # Persist the two subsets
    NORMALIZED_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    normalized_df.to_csv(NORMALIZED_CSV_PATH, index=False)
    raw_df.to_csv(RAW_CSV_PATH, index=False)
    logger.info(f"Normalized subset written to {NORMALIZED_CSV_PATH} ({len(normalized_df)} rows)")
    logger.info(f"Raw subset written to {RAW_CSV_PATH} ({len(raw_df)} rows)")

    # Prepare stratification column – prefer source_id if present, else normalization_method
    stratify_col = "source_id" if "source_id" in df.columns else "normalization_method"
    stratify_vals = df[stratify_col]

    # Perform stratified split (20% test)
    splitter = StratifiedShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=42,
    )
    train_idx, test_idx = next(splitter.split(df, stratify_vals))

    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # Write splits
    TRAIN_SPLIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_SPLIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(TRAIN_SPLIT_PATH, index=False)
    test_df.to_csv(TEST_SPLIT_PATH, index=False)
    logger.info(f"Train split written to {TRAIN_SPLIT_PATH} ({len(train_df)} rows)")
    logger.info(f"Test  split written to {TEST_SPLIT_PATH} ({len(test_df)} rows)")

    # Summary JSON
    summary = {
        "total_count": int(len(df)),
        "normalized_count": int(len(normalized_df)),
        "raw_count": int(len(raw_df)),
        "train_count": int(len(train_df)),
        "test_count": int(len(test_df)),
    }
    SPLIT_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SPLIT_SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Split summary written to {SPLIT_SUMMARY_PATH}")

    return summary

def main() -> int:
    """
    Entry point used by `python -m code.main preprocess`.
    Executes the three preprocessing stages in order.
    Returns 0 on success, non‑zero on failure.
    """
    logger = get_logger(__name__)
    try:
        # Load merged data
        merged_df = _load_merged()

        # 1. Drop rows with missing required predictors
        dropped_df = handle_missing_values(merged_df)

        # 2. Apply Archard normalization (adds K and flag)
        clean_df = archard_normalization(dropped_df)

        # 3. Perform dataset splitting and write summary artefacts
        split_dataset(clean_df)

        logger.info("Preprocess step completed successfully.")
        return 0
    except Exception as exc:
        logger.error(f"Preprocess failed: {exc}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
