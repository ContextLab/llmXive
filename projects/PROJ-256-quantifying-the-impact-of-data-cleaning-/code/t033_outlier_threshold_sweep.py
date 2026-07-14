"""
Outlier‑threshold sweep (Task T033)

For a set of IQR multiplier thresholds *k* the script:
  1. Loads the raw dataset.
  2. Applies ``apply_iqr_outlier_removal`` with the current *k*.
  3. Runs the baseline statistical analysis on the cleaned data.
  4. Generates a *null* dataset by shuffling the outcome column and
     re‑running the analysis.
  5. Computes:
     - **FPR** (False‑Positive Rate): proportion of null analyses where
       p ≤ 0.05.
     - **Inconsistency Rate**: proportion of datasets where the significance
       decision (p ≤ 0.05) differs between the raw and cleaned analyses.
  6. Writes a JSON file ``data/processed/outlier_threshold_sweep.json``
     containing the metrics for each threshold.
"""

import json
import logging
import os
import random
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd

from utils import setup_logging, pin_random_seed
from cleaning import apply_iqr_outlier_removal
from analysis import run_baseline_analysis
from data_loader import ensure_data_exists, load_datasets_from_raw

logger = setup_logging(log_level="INFO")
pin_random_seed(1234)


def _load_first_raw_dataset() -> pd.DataFrame:
    """
    Ensure raw data exists and return the first CSV as a DataFrame.
    """
    raw_dir = Path("data/raw")
    ensure_data_exists()
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")
    df = pd.read_csv(csv_files[0])
    logger.info(f"Loaded raw dataset from {csv_files[0]}")
    return df


def _determine_outcome_column(df: pd.DataFrame) -> str:
    """
    Heuristic to pick an outcome column: the first numeric column.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        raise ValueError("Dataset contains no numeric columns to infer outcome.")
    return numeric_cols[0]


def _run_analysis(df: pd.DataFrame, outcome: str) -> Dict[str, Any]:
    """
    Wrapper around ``run_baseline_analysis`` that forces the same
    outcome column for consistency across raw/cleaned/null runs.
    """
    return run_baseline_analysis(dataframe=df, outcome=outcome)


def main(thresholds: List[float] = None) -> None:
    if thresholds is None:
        thresholds = [1.0, 1.5, 2.0]  # default sweep values

    raw_df = _load_first_raw_dataset()
    outcome_col = _determine_outcome_column(raw_df)

    # Baseline metrics on the *raw* data – used for inconsistency calculation
    raw_metrics = _run_analysis(raw_df, outcome_col)
    raw_p = raw_metrics.get("t_test", {}).get("p_value")
    raw_sig = raw_p is not None and raw_p <= 0.05

    sweep_results: Dict[str, Dict[str, Any]] = {}

    for k in thresholds:
        logger.info(f"Applying IQR outlier removal with k={k}")
        cleaned_df = apply_iqr_outlier_removal(raw_df.copy(), k=k)

        # Baseline analysis on cleaned data
        cleaned_metrics = _run_analysis(cleaned_df, outcome_col)
        cleaned_p = cleaned_metrics.get("t_test", {}).get("p_value")
        cleaned_sig = cleaned_p is not None and cleaned_p <= 0.05

        # --- Null dataset generation (permutation of outcome) -------------
        null_df = cleaned_df.copy()
        null_df[outcome_col] = np.random.permutation(null_df[outcome_col].values)
        null_metrics = _run_analysis(null_df, outcome_col)
        null_p = null_metrics.get("t_test", {}).get("p_value")
        null_sig = null_p is not None and null_p <= 0.05

        # Compute rates
        fpr = 1.0 if null_sig else 0.0
        inconsistency = 1.0 if (raw_sig != cleaned_sig) else 0.0

        sweep_results[str(k)] = {
            "false_positive_rate": fpr,
            "inconsistency_rate": inconsistency,
            "raw_p": raw_p,
            "cleaned_p": cleaned_p,
            "null_p": null_p
        }

        logger.info(
            f"k={k}: FPR={fpr:.3f}, Inconsistency={inconsistency:.3f}, "
            f"raw_p={raw_p:.4f}, cleaned_p={cleaned_p:.4f}, null_p={null_p:.4f}"
        )

    output_path = Path("data/processed/outlier_threshold_sweep.json")
    os.makedirs(output_path.parent, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(sweep_results, f, indent=2)
    logger.info(f"Outlier‑threshold sweep results written to {output_path}")


if __name__ == "__main__":
    main()
