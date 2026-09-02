"""
T021d: Sensitivity Analysis for Plant Disease Resistance Model.

Performs a sweep of probability decision thresholds to report False Positive Rate (FPR)
and False Negative Rate (FNR) at each step.

Handles two scenarios based on sample size (N):
1. N >= 50: Uses the independent hold-out set defined in split_indices.json.
2. N < 50: Uses the full dataset (learning curve scenario).

Output: results/sensitivity_analysis.json
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.constants import DATA_PROCESSED_DIR, RESULTS_DIR
from utils.io import ensure_dirs
from modeling.evaluate import load_model_and_indices, load_processed_data


def calculate_fpr_fnr(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> Tuple[float, float]:
    """
    Calculate False Positive Rate and False Negative Rate for a given threshold.

    Args:
        y_true: True binary labels (0 or 1).
        y_prob: Predicted probabilities for class 1.
        threshold: Decision threshold.

    Returns:
        Tuple of (FPR, FNR).
    """
    y_pred = (y_prob >= threshold).astype(int)

    # Confusion matrix components
    # TP: True Positive, FP: False Positive, TN: True Negative, FN: False Negative
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    # Calculate rates
    # FPR = FP / (FP + TN)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    # FNR = FN / (FN + TP)
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    return fpr, fnr


def run_sensitivity_analysis(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    thresholds: List[float]
) -> List[Dict[str, float]]:
    """
    Run sensitivity analysis over a list of thresholds.

    Args:
        y_true: True binary labels.
        y_prob: Predicted probabilities.
        thresholds: List of thresholds to evaluate.

    Returns:
        List of dictionaries containing threshold, FPR, and FNR.
    """
    results = []
    for thresh in thresholds:
        fpr, fnr = calculate_fpr_fnr(y_true, y_prob, thresh)
        results.append({
            "threshold": float(thresh),
            "fpr": float(fpr),
            "fnr": float(fnr)
        })
    return results


def main():
    """
    Main entry point for T021d Sensitivity Analysis.
    """
    ensure_dirs(RESULTS_DIR)
    output_path = Path(RESULTS_DIR) / "sensitivity_analysis.json"

    print("Loading processed data and model indices...")
    try:
        X, y = load_processed_data()
        model, split_indices = load_model_and_indices()
    except Exception as e:
        print(f"Error loading data or model: {e}")
        sys.exit(1)

    n_samples = len(y)
    print(f"Total samples: {n_samples}")

    # Determine which dataset to use based on N
    use_holdout = n_samples >= 50
    print(f"Using hold-out set: {use_holdout} (N >= 50: {use_holdout})")

    if use_holdout:
        if not split_indices or "holdout_indices" not in split_indices:
            print("Error: Hold-out indices not found in split_indices.json but N >= 50.")
            sys.exit(1)

        holdout_idx = np.array(split_indices["holdout_indices"])
        y_true = y[holdout_idx]

        # Load model and predict on hold-out set
        X_holdout = X.iloc[holdout_idx] if isinstance(X, pd.DataFrame) else X[holdout_idx]
        y_prob = model.predict_proba(X_holdout)[:, 1]
        print(f"Running sensitivity analysis on {len(y_true)} hold-out samples.")
    else:
        # N < 50: Use full dataset
        y_true = y
        if isinstance(X, pd.DataFrame):
            y_prob = model.predict_proba(X)[:, 1]
        else:
            y_prob = model.predict_proba(X)[:, 1]
        print(f"Running sensitivity analysis on full dataset ({len(y_true)} samples).")

    # Define threshold sweep
    # Sweep from 0.0 to 1.0 with steps of 0.05 (21 points)
    thresholds = np.arange(0.0, 1.05, 0.05).tolist()

    print(f"Running threshold sweep with {len(thresholds)} steps...")
    analysis_results = run_sensitivity_analysis(y_true, y_prob, thresholds)

    # Prepare output structure
    output_data = {
        "n_samples": int(n_samples),
        "used_holdout": use_holdout,
        "thresholds_evaluated": len(thresholds),
        "results": analysis_results
    }

    # Write output
    print(f"Writing results to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print("Sensitivity analysis complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
