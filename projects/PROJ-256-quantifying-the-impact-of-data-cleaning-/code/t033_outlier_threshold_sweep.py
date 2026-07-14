import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from cleaning import apply_iqr_outlier_removal
from analysis import run_baseline_analysis
from utils import setup_logging, pin_random_seed

logger = setup_logging(log_level="INFO")

def load_json(path: str) -> Dict[str, Any]:
    """Utility to load a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_fpr(null_results: List[Dict[str, Any]]) -> float:
    """
    False Positive Rate: proportion of null analyses where the t‑test p‑value
    is ≤ 0.05.
    """
    if not null_results:
        return 0.0
    count = sum(1 for r in null_results if r.get("t_test", {}).get("p_value", 1) <= 0.05)
    return count / len(null_results)

def compute_inconsistency_rate(baseline_res: Dict[str, Any],
                              cleaned_res: Dict[str, Any]) -> float:
    """
    Inconsistency Rate: proportion of datasets where significance status
    (p ≤ 0.05) changes between baseline and cleaned results.
    For a single dataset this is either 0 or 1.
    """
    base_sig = baseline_res.get("t_test", {}).get("p_value", 1) <= 0.05
    clean_sig = cleaned_res.get("t_test", {}).get("p_value", 1) <= 0.05
    return 0.0 if base_sig == clean_sig else 1.0

def main() -> None:
    """
    Perform an outlier‑threshold sweep (varying the IQR multiplier ``k``)
    and compute both the false‑positive rate on null datasets and the
    inconsistency rate between baseline and cleaned analyses.

    The resulting metrics are written to:
        data/processed/null_fpr_metrics.json
    """
    # Ensure reproducibility for the null‑shuffle step
    pin_random_seed(42)

    raw_dir = Path("data/raw")
    if not raw_dir.is_dir():
        logger.error("Raw data directory %s does not exist.", raw_dir)
        raise FileNotFoundError(f"{raw_dir} not found")

    # Load the first CSV in the raw directory
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.error("No CSV files found in %s.", raw_dir)
        raise FileNotFoundError(f"No CSV in {raw_dir}")
    df_raw = pd.read_csv(csv_files[0])

    # Define the sweep values for the IQR multiplier
    ks = [0.5, 1.0, 1.5, 2.0, 2.5]

    sweep_results: List[Dict[str, Any]] = []

    # Baseline result on the untouched raw data (used for inconsistency)
    baseline_res = run_baseline_analysis(dataframe=df_raw)

    for k in ks:
        logger.info("Processing IQR outlier removal with k=%.2f", k)

        # Apply outlier removal
        df_clean = apply_iqr_outlier_removal(df_raw, k=k)

        # Re‑run analysis on the cleaned data
        cleaned_res = run_baseline_analysis(dataframe=df_clean)

        # Generate a null dataset by shuffling the outcome column
        outcome_col = baseline_res["metadata"]["outcome"]
        df_null = df_raw.copy()
        df_null[outcome_col] = np.random.permutation(df_null[outcome_col].values)

        # Run analysis on the null dataset (single run is sufficient for FPR)
        null_res = run_baseline_analysis(dataframe=df_null)

        fpr = compute_fpr([null_res])
        inconsistency = compute_inconsistency_rate(baseline_res, cleaned_res)

        sweep_results.append(
            {
                "k": k,
                "false_positive_rate": round(fpr, 3),
                "inconsistency_rate": round(inconsistency, 3),
            }
        )
        logger.debug(
            "k=%.2f -> FPR: %.3f, Inconsistency: %.3f",
            k,
            fpr,
            inconsistency,
        )

    # Write the sweep metrics to the declared output location
    output_path = Path("data/processed/null_fpr_metrics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(sweep_results, f, indent=2)

    logger.info("Outlier‑threshold sweep completed. Results saved to %s", output_path)

if __name__ == "__main__":
    main()
