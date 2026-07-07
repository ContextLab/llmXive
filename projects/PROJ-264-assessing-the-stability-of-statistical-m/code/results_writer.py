"""
Module to write raw evaluation results to CSV.
Implements T014: Write raw evaluation results to results/raw_evaluations.csv.
"""
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

logger = logging.getLogger(__name__)

# Ensure the results directory exists
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

RAW_EVAL_FILE = RESULTS_DIR / "raw_evaluations.csv"

# Expected columns as per task specification
EXPECTED_COLUMNS = [
    "dataset_id",
    "model_name",
    "fold_id",
    "repeat_id",
    "accuracy",
    "f1_score"
]


def write_raw_evaluations(results: List[Dict[str, Any]]) -> None:
    """
    Write a list of evaluation result dictionaries to results/raw_evaluations.csv.

    The output file must have the exact columns:
    dataset_id, model_name, fold_id, repeat_id, accuracy, f1_score

    Args:
        results: List of dicts containing evaluation metrics from the CV loop.
                 Each dict should have keys matching EXPECTED_COLUMNS.
    """
    if not results:
        logger.warning("No results to write. Creating an empty CSV with headers.")
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)
        df.to_csv(RAW_EVAL_FILE, index=False)
        logger.info(f"Created empty results file at {RAW_EVAL_FILE}")
        return

    # Validate that all expected columns are present in at least one row
    # (We assume consistent structure across all results)
    first_row_keys = set(results[0].keys())
    missing_cols = set(EXPECTED_COLUMNS) - first_row_keys
    if missing_cols:
        raise ValueError(
            f"Missing expected columns in results data: {missing_cols}. "
            f"Found keys: {first_row_keys}"
        )

    df = pd.DataFrame(results)

    # Ensure column order matches specification
    df = df[EXPECTED_COLUMNS]

    # Ensure numeric columns are correctly typed
    numeric_cols = ["accuracy", "f1_score", "fold_id", "repeat_id", "dataset_id"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.to_csv(RAW_EVAL_FILE, index=False)
    logger.info(
        f"Wrote {len(df)} evaluation records to {RAW_EVAL_FILE}. "
        f"Columns: {list(df.columns)}"
    )


def append_raw_evaluations(results: List[Dict[str, Any]]) -> None:
    """
    Append evaluation results to the existing results/raw_evaluations.csv file.
    If the file does not exist, it will be created with headers.

    Args:
        results: List of dicts containing evaluation metrics.
    """
    if not results:
        return

    df_new = pd.DataFrame(results)
    
    # Ensure column order
    if not all(col in df_new.columns for col in EXPECTED_COLUMNS):
       raise ValueError("New results missing required columns.")
    df_new = df_new[EXPECTED_COLUMNS]

    if RAW_EVAL_FILE.exists():
        df_existing = pd.read_csv(RAW_EVAL_FILE)
        # Verify schema match before appending
        if list(df_existing.columns) != EXPECTED_COLUMNS:
            raise ValueError(
                f"Existing file schema mismatch. Expected {EXPECTED_COLUMNS}, "
                f"found {list(df_existing.columns)}"
            )
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_csv(RAW_EVAL_FILE, index=False)
        logger.info(
            f"Appended {len(df_new)} records to {RAW_EVAL_FILE}. "
            f"Total records: {len(df_combined)}"
        )
    else:
        df_new.to_csv(RAW_EVAL_FILE, index=False)
        logger.info(f"Created and wrote {len(df_new)} records to {RAW_EVAL_FILE}")
