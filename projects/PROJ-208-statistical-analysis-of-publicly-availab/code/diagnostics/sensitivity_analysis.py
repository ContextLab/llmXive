"""
Sensitivity Analysis for Issue Resolution Thresholds (FR-007).

This module performs a sensitivity analysis by sweeping a range of cutoffs
to determine how classification of "fast" vs "slow" resolved issues changes
based on the threshold. It calculates false-positive and false-negative rates
relative to a reference standard (e.g., a specific domain-expert cutoff or
a statistically derived cutoff like the median).

It reports:
- Threshold sensitivity table (cutoff, TP, TN, FP, FN, Precision, Recall, F1)
- False-positive and False-negative rates across the sweep.
- Identification of the optimal cutoff based on F1 score or balanced accuracy.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

# Import shared config for paths
from utils.config import get_config, get_path

# Import data loader from cross_validation to ensure consistency
# Note: cross_validation.py is in analysis/, so we need to adjust import path
# Since we are in diagnostics/, we need to go up to code/ then into analysis
# However, the API surface shows `from analysis.cross_validation import ...`
# We will implement a local loader to avoid circular dependency issues if any,
# but strictly follow the API surface for `load_cleaned_data`.
# The API surface shows `load_cleaned_data` in `analysis.cross_validation`.
# We will import it there.
from analysis.cross_validation import load_cleaned_data

logger = logging.getLogger(__name__)


def calculate_metrics_at_cutoff(
    resolution_times: np.ndarray,
    cutoff: float,
    reference_cutoff: float
) -> Dict[str, float]:
    """
    Calculate confusion matrix metrics at a specific cutoff relative to a reference.

    Parameters
    ----------
    resolution_times : np.ndarray
        Array of resolution times in hours.
    cutoff : float
        The threshold being tested.
    reference_cutoff : float
        The "ground truth" threshold (e.g., domain expert definition of 'fast').

    Returns
    -------
    Dict[str, float]
        Dictionary containing TP, TN, FP, FN, Precision, Recall, F1, etc.
    """
    # Binary classification: 1 = Fast (resolved <= cutoff), 0 = Slow
    # Ground Truth based on reference_cutoff
    y_true = (resolution_times <= reference_cutoff).astype(int)
    # Predicted based on current cutoff
    y_pred = (resolution_times <= cutoff).astype(int)

    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    # Calculate rates
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # False Positive Rate (FPR) = FP / (FP + TN)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    # False Negative Rate (FNR) = FN / (FN + TP)
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    return {
        "cutoff": cutoff,
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
        "fnr": fnr,
        "accuracy": (tp + tn) / len(resolution_times) if len(resolution_times) > 0 else 0.0
    }


def run_sensitivity_analysis(
    resolution_times: np.ndarray,
    reference_cutoff: Optional[float] = None,
    cutoff_range: Optional[Tuple[float, float, int]] = None
) -> List[Dict[str, Any]]:
    """
    Run the sensitivity analysis sweeping across a range of cutoffs.

    Parameters
    ----------
    resolution_times : np.ndarray
        Array of resolution times.
    reference_cutoff : float, optional
        The reference threshold to treat as "truth". Defaults to median if None.
    cutoff_range : Tuple(min, max, steps), optional
        Range of cutoffs to test. Defaults to (10th percentile, 90th percentile, 50 steps).

    Returns
    -------
    List[Dict[str, Any]]
        List of metric dictionaries for each cutoff tested.
    """
    if len(resolution_times) == 0:
        logger.warning("No resolution times provided for sensitivity analysis.")
        return []

    # Determine reference cutoff if not provided
    if reference_cutoff is None:
        reference_cutoff = float(np.median(resolution_times))
        logger.info(f"Using median ({reference_cutoff:.2f}h) as reference cutoff.")

    # Determine cutoff range if not provided
    if cutoff_range is None:
        min_val = float(np.percentile(resolution_times, 10))
        max_val = float(np.percentile(resolution_times, 90))
        steps = 50
    else:
        min_val, max_val, steps = cutoff_range

    logger.info(f"Running sensitivity analysis from {min_val:.2f}h to {max_val:.2f}h ({steps} steps)")

    results = []
    cutoffs = np.linspace(min_val, max_val, steps)

    for cutoff in cutoffs:
        metrics = calculate_metrics_at_cutoff(resolution_times, cutoff, reference_cutoff)
        results.append(metrics)

    return results


def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save sensitivity analysis results to a JSON file.

    Parameters
    ----------
    results : List[Dict[str, Any]]
        List of metric dictionaries.
    output_path : Path
        Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Sensitivity analysis results saved to {output_path}")


def main() -> int:
    """
    Main entry point for sensitivity analysis.

    Returns
    -------
    int
        Exit code (0 for success, 1 for failure).
    """
    config = get_config()
    data_path = get_path("cleaned_issues")
    output_dir = get_path("figures") # Using figures dir for JSON as per project structure convention for analysis outputs? No, processed is better.
    # Re-check paths: data/processed/ is for processed data.
    # Let's define the output path explicitly based on project structure.
    # The task asks for output in code/diagnostics/sensitivity_analysis.py but the
    # results should be saved to data/processed/ or similar.
    # Let's use data/processed/sensitivity_analysis.json
    output_path = Path("data/processed/sensitivity_analysis.json")

    try:
        # Load data
        logger.info(f"Loading cleaned data from {data_path}")
        df = load_cleaned_data(data_path)

        if 'resolution_time_hours' not in df.columns:
            logger.error("Column 'resolution_time_hours' not found in dataset.")
            return 1

        times = df['resolution_time_hours'].dropna().to_numpy()

        if len(times) == 0:
            logger.error("No valid resolution times found in dataset.")
            return 1

        # Run analysis
        results = run_sensitivity_analysis(times)

        # Save results
        save_results(results, output_path)

        # Print summary
        logger.info("Sensitivity Analysis Summary:")
        logger.info(f"Total data points: {len(times)}")
        logger.info(f"Reference cutoff (median): {np.median(times):.2f}h")

        # Find best cutoff (max F1)
        if results:
            best = max(results, key=lambda x: x['f1'])
            logger.info(f"Best cutoff by F1: {best['cutoff']:.2f}h (F1={best['f1']:.4f})")
            logger.info(f"False Positive Rate at best: {best['fpr']:.4f}")
            logger.info(f"False Negative Rate at best: {best['fnr']:.4f}")

        return 0

    except Exception as e:
        logger.exception(f"Error during sensitivity analysis: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
