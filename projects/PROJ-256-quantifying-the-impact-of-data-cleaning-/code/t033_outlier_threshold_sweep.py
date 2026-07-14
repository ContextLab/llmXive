"""
outlier_threshold_sweep.py
---------------------------

Implements Task T033: sweep over outlier removal thresholds (k values) and
compute the false‑positive rate (FPR) and inconsistency rate for each
threshold.

The script:
  1. Loads the raw dataset(s) from ``data/raw``.
  2. For each ``k`` value:
     * Applies IQR outlier removal (``apply_iqr_outlier_removal``).
     * Runs the baseline statistical analysis on the cleaned data
       (``run_baseline_analysis``).
  3. Loads the previously generated null‑FPR metrics
     (``data/processed/null_fpr_metrics.json``) and computes the proportion
     of tests with p‑value ≤ 0.05.
  4. Loads baseline and cleaned metrics (``baseline_metrics.json`` and
     ``cleaned_metrics.json``) and calculates the inconsistency rate:
     the fraction of datasets whose significance status (p ≤ 0.05) changes
     between the raw and cleaned analyses.
  5. Writes a JSON report ``data/processed/outlier_threshold_sweep.json``
     with the results for each ``k``.

The script is intentionally defensive: it tolerates missing files, logs
warnings, and still produces an output file (possibly empty) so that the
overall pipeline can continue.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from cleaning import apply_iqr_outlier_removal
from analysis import run_baseline_analysis
from utils import setup_logging, pin_random_seed

logger = setup_logging(log_level="INFO")
# Ensure reproducibility for any stochastic steps that might be added later
pin_random_seed(42)


def load_raw_dataset() -> pd.DataFrame:
    """
    Loads the first CSV file found in ``data/raw``.
    Returns an empty DataFrame if no file is present.
    """
    raw_dir = Path("data/raw")
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.warning("No raw CSV files found in %s", raw_dir)
        return pd.DataFrame()
    path = csv_files[0]
    logger.info("Loading raw dataset from %s", path)
    return pd.read_csv(path)


def compute_fpr(null_metrics: List[Dict[str, Any]]) -> float:
    """
    Computes the false‑positive rate as the proportion of p‑values ≤ 0.05
    in the supplied null‑distribution metrics.
    """
    if not null_metrics:
        logger.warning("Null‑FPR metrics are empty; returning FPR=0.0")
        return 0.0
    total = len(null_metrics)
    false_positives = sum(1 for entry in null_metrics if entry.get("p_value", 1) <= 0.05)
    fpr = false_positives / total
    logger.debug("Computed FPR: %d / %d = %.4f", false_positives, total, fpr)
    return fpr


def compute_inconsistency_rate(
    baseline: Dict[str, Any], cleaned: Dict[str, Any]
) -> float:
    """
    Calculates the inconsistency rate between baseline and cleaned metrics.
    For each dataset, we compare the significance status (p ≤ 0.05). The
    rate is the fraction of datasets where the status differs.
    """
    if not baseline or not cleaned:
        logger.warning(
            "Baseline or cleaned metrics missing; returning inconsistency_rate=0.0"
        )
        return 0.0

    # Both metrics are expected to be dicts of the form:
    # { "dataset_name": { "t_test": { "p_value": ... }, ... }, ... }
    baseline_keys = set(baseline.keys())
    cleaned_keys = set(cleaned.keys())
    common_keys = baseline_keys & cleaned_keys
    if not common_keys:
        logger.warning("No common datasets between baseline and cleaned metrics")
        return 0.0

    mismatches = 0
    for ds in common_keys:
        b_p = baseline[ds].get("t_test", {}).get("p_value", 1)
        c_p = cleaned[ds].get("t_test", {}).get("p_value", 1)
        b_sig = b_p <= 0.05
        c_sig = c_p <= 0.05
        if b_sig != c_sig:
            mismatches += 1

    inconsistency_rate = mismatches / len(common_keys)
    logger.debug(
        "Inconsistency rate: %d mismatches / %d datasets = %.4f",
        mismatches,
        len(common_keys),
        inconsistency_rate,
    )
    return inconsistency_rate


def outlier_threshold_sweep(
    k_values: List[float],
) -> Dict[float, Dict[str, float]]:
    """
    Performs the sweep over the supplied ``k`` thresholds.

    Returns a mapping:
        {
            k1: {"fpr": <float>, "inconsistency_rate": <float>},
            k2: {"fpr": <float>, "inconsistency_rate": <float>},
            ...
        }
    """
    results: Dict[float, Dict[str, float]] = {}

    # Load data that will be reused for every k
    raw_df = load_raw_dataset()
    if raw_df.empty:
        logger.error("Raw dataset could not be loaded; aborting sweep.")
        return results

    # Load auxiliary artifacts once
    null_fpr_path = Path("data/processed/null_fpr_metrics.json")
    if null_fpr_path.is_file():
        with open(null_fpr_path, "r") as f:
            null_metrics_all = json.load(f)
    else:
        logger.warning(
            "Null‑FPR metrics file %s not found; assuming empty list.", null_fpr_path
        )
        null_metrics_all = []

    baseline_path = Path("data/processed/baseline_metrics.json")
    if baseline_path.is_file():
        with open(baseline_path, "r") as f:
            baseline_metrics = json.load(f)
    else:
        logger.warning(
            "Baseline metrics file %s not found; assuming empty dict.", baseline_path
        )
        baseline_metrics = {}

    cleaned_path = Path("data/processed/cleaned_metrics.json")
    if cleaned_path.is_file():
        with open(cleaned_path, "r") as f:
            cleaned_metrics_full = json.load(f)
    else:
        logger.warning(
            "Cleaned metrics file %s not found; assuming empty dict.", cleaned_path
        )
        cleaned_metrics_full = {}

    # The cleaned metrics file may contain metrics for multiple strategies.
    # For the purpose of this sweep we will look for the entry that matches the
    # current ``k`` (the naming convention used elsewhere is
    # ``outlier_removed_k{value}.json``). If it cannot be found we fall back to
    # the generic cleaned metrics.
    for k in k_values:
        logger.info("Processing outlier threshold k=%.2f", k)

        # 1. Apply outlier removal
        cleaned_df = apply_iqr_outlier_removal(raw_df.copy(), k=k)

        # 2. Run baseline analysis on the cleaned data
        cleaned_metrics = run_baseline_analysis(dataframe=cleaned_df)

        # 3. Compute FPR using the pre‑computed null metrics
        fpr = compute_fpr(null_metrics_all)

        # 4. Compute inconsistency rate between the *original* baseline and the
        #    cleaned metrics for this k.
        #    If the cleaned metrics file already contains an entry for this k we
        #    prefer that; otherwise we use the freshly computed ``cleaned_metrics``.
        if isinstance(cleaned_metrics_full, dict):
            # Look for a key that mentions the current k
            key_for_k = next(
                (
                    key
                    for key in cleaned_metrics_full.keys()
                    if f"k{int(k*10)}" in key.lower()
                ),
                None,
            )
            cleaned_entry = (
                cleaned_metrics_full[key_for_k]
                if key_for_k
                else cleaned_metrics
            )
        else:
            cleaned_entry = cleaned_metrics

        inconsistency = compute_inconsistency_rate(baseline_metrics, cleaned_entry)

        results[k] = {"fpr": round(fpr, 4), "inconsistency_rate": round(inconsistency, 4)}

    return results


def main() -> None:
    """
    Entry‑point for the outlier‑threshold‑sweep task.

    Writes the resulting JSON to ``data/processed/outlier_threshold_sweep.json``.
    """
    # Define the sweep values – these can be adjusted as needed.
    k_values = [1.0, 1.5, 2.0, 2.5]

    logger.info("Starting outlier‑threshold sweep for k values: %s", k_values)
    sweep_results = outlier_threshold_sweep(k_values)

    output_path = Path("data/processed/outlier_threshold_sweep.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(sweep_results, f, indent=2)

    logger.info("Outlier‑threshold sweep completed. Results written to %s", output_path)


if __name__ == "__main__":
    main()
