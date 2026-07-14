import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List

from utils import setup_logging
from cleaning import apply_iqr_outlier_removal
from analysis import run_baseline_analysis
import pandas as pd

logger = setup_logging("INFO")

def load_json(path: str) -> Dict[str, Any]:
    """Load a JSON file; return empty dict if file does not exist."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File {path} not found; returning empty dict.")
        return {}

def compute_fpr(null_metrics: Dict[str, Any]) -> float:
    """
    False‑positive rate: proportion of predictor tests where p ≤ 0.05
    in the null (permuted) metrics.
    """
    if not null_metrics:
        return 0.0
    total = 0
    positives = 0
    for pred, res in null_metrics.get("predictors", {}).items():
        p = res.get("t_test", {}).get("p_value") or res.get("regression", {}).get("p_value")
        if p is not None:
            total += 1
            if p <= 0.05:
                positives += 1
    return positives / total if total else 0.0

def compute_inconsistency_rate(baseline: Dict[str, Any],
                               cleaned: Dict[str, Any]) -> float:
    """
    Inconsistency Rate: proportion of predictors where significance status
    (p ≤ 0.05) differs between baseline and cleaned results.
    """
    if not baseline or not cleaned:
        return 0.0
    total = 0
    diff = 0
    for pred, base_res in baseline.get("predictors", {}).items():
        clean_res = cleaned.get("predictors", {}).get(pred)
        if not clean_res:
            continue
        base_p = base_res.get("t_test", {}).get("p_value") or base_res.get("regression", {}).get("p_value")
        clean_p = clean_res.get("t_test", {}).get("p_value") or clean_res.get("regression", {}).get("p_value")
        if base_p is None or clean_p is None:
            continue
        total += 1
        if (base_p <= 0.05) != (clean_p <= 0.05):
            diff += 1
    return diff / total if total else 0.0

def main():
    """
    Perform an outlier‑threshold sweep.

    For each k in the predefined list we:
    1. Load the raw dataset (first CSV under data/raw/).
    2. Apply IQR outlier removal with the current k.
    3. Run baseline analysis on the cleaned data and write metrics.
    4. Generate a null dataset by shuffling the outcome column,
       run analysis, and compute the false‑positive rate.
    5. Compute inconsistency rate against the original baseline.
    6. Persist all artefacts under data/processed/.
    """
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load raw data (use first CSV)
    raw_files = list(raw_dir.glob("*.csv"))
    if not raw_files:
        logger.error("No raw CSV files found in data/raw")
        return
    df_raw = pd.read_csv(raw_files[0])

    # Baseline metrics on raw data (used for inconsistency calculations)
    baseline_metrics = run_baseline_analysis(df_raw)
    baseline_path = processed_dir / "baseline_metrics.json"
    with open(baseline_path, "w", encoding="utf-8") as f:
        json.dump(baseline_metrics, f, indent=2)
    logger.info(f"Wrote baseline metrics to {baseline_path}")

    # Define sweep thresholds
    thresholds = [1.0, 1.5, 2.0, 2.5]

    sweep_results: List[Dict[str, Any]] = []

    for k in thresholds:
        logger.info(f"Processing outlier threshold k={k}")
        # Clean data
        df_clean = apply_iqr_outlier_removal(df_raw.copy(), k=k)

        # Analyse cleaned data
        cleaned_metrics = run_baseline_analysis(df_clean)
        cleaned_path = processed_dir / f"cleaned_metrics_k_{k}.json"
        with open(cleaned_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_metrics, f, indent=2)

        # Create null dataset by shuffling the outcome column
        outcome_col = baseline_metrics.get("outcome")
        if outcome_col and outcome_col in df_clean.columns:
            df_null = df_clean.copy()
            df_null[outcome_col] = np.random.permutation(df_null[outcome_col].values)
            null_metrics = run_baseline_analysis(df_null)
            null_path = processed_dir / f"null_fpr_metrics_k_{k}.json"
            with open(null_path, "w", encoding="utf-8") as f:
                json.dump(null_metrics, f, indent=2)
        else:
            null_metrics = {}
            null_path = None

        fpr = compute_fpr(null_metrics)
        inc_rate = compute_inconsistency_rate(baseline_metrics, cleaned_metrics)

        sweep_entry = {
            "k": k,
            "cleaned_metrics_path": str(cleaned_path),
            "null_metrics_path": str(null_path) if null_path else None,
            "false_positive_rate": round(fpr, 4),
            "inconsistency_rate": round(inc_rate, 4),
        }
        sweep_results.append(sweep_entry)
        logger.info(f"Threshold {k}: FPR={fpr:.4f}, Inconsistency={inc_rate:.4f}")

    # Write sweep summary
    sweep_path = processed_dir / "outlier_threshold_sweep.json"
    with open(sweep_path, "w", encoding="utf-8") as f:
        json.dump(sweep_results, f, indent=2)
    logger.info(f"Wrote outlier‑threshold sweep summary to {sweep_path}")

if __name__ == "__main__":
    main()