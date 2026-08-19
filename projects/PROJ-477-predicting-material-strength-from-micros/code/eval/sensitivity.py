"""Sensitivity analysis for binary classification thresholds.

Implements FR-007: Sensitivity Analysis on prediction thresholds.
Binarizes using the median predicted strength of the test set.
Sweeps thresholds across a representative set of low absolute difference values.
Computes FPR/FNR for each threshold.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Import shared utilities
from utils.config import get_results_dir, set_seed, get_seed
from utils.logging_config import get_logger, LogEntry

# Ensure we can import from code root if run as script
if __name__ == "__main__":
    # Add parent to path for imports when running directly
    parent = Path(__file__).resolve().parent.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))


def setup_logging() -> logging.Logger:
    """Setup logger for sensitivity analysis."""
    logger = get_logger("sensitivity")
    logger.setLevel(logging.INFO)
    return logger


def load_predictions(predictions_path: str) -> Tuple[List[float], List[float]]:
    """Load predictions and true values from CSV.

    Args:
        predictions_path: Path to CSV with 'prediction' and 'true' columns.

    Returns:
        Tuple of (predictions_list, true_values_list)
    """
    predictions = []
    true_values = []

    with open(predictions_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle potential column name variations
            pred_key = 'prediction' if 'prediction' in row else 'predicted_strength'
            true_key = 'true' if 'true' in row else 'true_strength'
            predictions.append(float(row[pred_key]))
            true_values.append(float(row[true_key]))

    if not predictions:
        raise ValueError(f"No predictions found in {predictions_path}")

    return predictions, true_values


def binarize_by_median(predictions: List[float], true_values: List[float]) -> Tuple[List[int], List[int], float]:
    """Binarize predictions and true values using median predicted strength.

    Spec US-3 Scenario 2: Binarize using median predicted strength of the test set.
    True label is 1 if true_value >= median_prediction, else 0.
    Predicted label is 1 if prediction >= median_prediction, else 0.

    Args:
        predictions: List of predicted strength values.
        true_values: List of true strength values.

    Returns:
        Tuple of (binarized_predictions, binarized_true, median_threshold)
    """
    median_threshold = float(sorted(predictions)[len(predictions) // 2])

    binarized_predictions = [1 if p >= median_threshold else 0 for p in predictions]
    binarized_true = [1 if t >= median_threshold else 0 for t in true_values]

    return binarized_predictions, binarized_true, median_threshold


def compute_fpr_fnr(
    binarized_predictions: List[int],
    binarized_true: List[int],
    threshold: float
) -> Tuple[float, float]:
    """Compute False Positive Rate (FPR) and False Negative Rate (FNR) for a given threshold.

    For a specific threshold T:
    - Predicted 1 if pred >= T, else 0
    - True 1 if true >= T, else 0
    - FP: Predicted 1, True 0
    - FN: Predicted 0, True 1
    - TN: Predicted 0, True 0
    - TP: Predicted 1, True 1

    FPR = FP / (FP + TN)  [Rate of false alarms among actual negatives]
    FNR = FN / (FN + TP)  [Rate of missed detections among actual positives]

    Args:
        binarized_predictions: Binarized predictions based on median.
        binarized_true: Binarized true values based on median.
        threshold: The specific threshold to evaluate.

    Returns:
        Tuple of (FPR, FNR)
    """
    fp = tn = tp = fn = 0

    for pred, true in zip(binarized_predictions, binarized_true):
        # Re-binarize relative to the current sweep threshold
        pred_bin = 1 if pred >= threshold else 0
        true_bin = 1 if true >= threshold else 0

        if pred_bin == 1 and true_bin == 0:
            fp += 1
        elif pred_bin == 0 and true_bin == 0:
            tn += 1
        elif pred_bin == 1 and true_bin == 0:
            # Already counted as FP
            pass
        elif pred_bin == 0 and true_bin == 1:
            fn += 1
        elif pred_bin == 1 and true_bin == 1:
            tp += 1

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    return fpr, fnr


def run_sensitivity_analysis(
    predictions: List[float],
    true_values: List[float],
    sweep_factor: float = 1.0,
    num_points: int = 11
) -> List[Dict[str, Any]]:
    """Run sensitivity analysis across a range of thresholds.

    Sweeps thresholds calculated as: median ± k * std
    where k ranges from -sweep_factor to +sweep_factor.

    Args:
        predictions: List of predicted values.
        true_values: List of true values.
        sweep_factor: Multiplier for std deviation to define sweep range.
        num_points: Number of points in the sweep (default 11 for -5 to +5 steps).

    Returns:
        List of dicts with threshold, fpr, fnr, sweep_factor.
    """
    import statistics

    median_val = statistics.median(predictions)
    std_val = statistics.stdev(predictions) if len(predictions) > 1 else 0.0

    # Generate k values: linearly spaced from -sweep_factor to +sweep_factor
    k_values = [
        -sweep_factor + (2 * sweep_factor * i / (num_points - 1))
        for i in range(num_points)
    ]

    results = []

    # Calculate baseline binarization based on median
    # Note: The spec says "Binarize using median predicted strength".
    # We interpret this as the baseline for "True" and "Predicted" labels being
    # relative to the median. However, FPR/FNR are typically calculated
    # relative to a decision threshold.
    #
    # Interpretation for this task:
    # 1. The "True" class (1) is defined as samples where True_Value >= Median_Pred.
    # 2. The "Predicted" class (1) is defined as samples where Pred_Value >= Threshold.
    # 3. We sweep Threshold around the Median_Pred.
    #
    # Wait, the spec says "Binarize using median... Sweep thresholds...".
    # This implies the binarization logic itself might change with the threshold.
    # Standard sensitivity analysis:
    # - True Label is fixed (e.g., based on a ground truth cutoff).
    # - Here, ground truth is continuous. We must define a ground truth binary label.
    # - Spec US-3 Scenario 2: "Binarize using median predicted strength".
    #   This likely means: Ground Truth 1 if True_Strength >= Median_Pred_Strength.
    #   Then we sweep the Decision Threshold for the model.
    #
    # Let's stick to the most robust interpretation:
    # Ground Truth 1: true_values >= median(predictions)
    # Model Prediction 1: predictions >= current_threshold
    # Sweep current_threshold around median(predictions).

    ground_truth_median = statistics.median(true_values) # Or use predictions median? Spec says "median predicted strength".
    # Spec: "Binarize using median predicted strength of the test set"
    # This defines the ground truth binary labels.
    ground_truth_bin = [1 if t >= median_val else 0 for t in true_values]

    for k in k_values:
        threshold = median_val + (k * std_val)
        
        # Calculate predictions at this threshold
        pred_bin = [1 if p >= threshold else 0 for p in predictions]

        # Compute FPR/FNR
        fp = sum(1 for p, t in zip(pred_bin, ground_truth_bin) if p == 1 and t == 0)
        tn = sum(1 for p, t in zip(pred_bin, ground_truth_bin) if p == 0 and t == 0)
        fn = sum(1 for p, t in zip(pred_bin, ground_truth_bin) if p == 0 and t == 1)
        tp = sum(1 for p, t in zip(pred_bin, ground_truth_bin) if p == 1 and t == 1)

        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        results.append({
            "threshold": threshold,
            "fpr": fpr,
            "fnr": fnr,
            "sweep_factor": k
        })

    return results


def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on model predictions.")
    parser.add_argument(
        "--predictions",
        required=True,
        help="Path to CSV file containing predictions (must have 'prediction' and 'true' columns)."
    )
    parser.add_argument(
        "--output",
        default="results/sensitivity_analysis.csv",
        help="Path to output CSV file."
    )
    parser.add_argument(
        "--sweep-factor",
        type=float,
        default=2.0,
        help="Multiplier for std deviation to define sweep range (default: 2.0)."
    )
    parser.add_argument(
        "--num-points",
        type=int,
        default=11,
        help="Number of points in the sweep (default: 11)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility."
    )

    args = parser.parse_args()

    # Setup
    logger = setup_logging()
    logger.info("Starting sensitivity analysis")

    if args.seed is not None:
        set_seed(args.seed)
        logger.info(f"Seed set to {args.seed}")

    # Validate input
    if not os.path.exists(args.predictions):
        logger.error(f"Predictions file not found: {args.predictions}")
        sys.exit(1)

    try:
        predictions, true_values = load_predictions(args.predictions)
        logger.info(f"Loaded {len(predictions)} predictions")
    except Exception as e:
        logger.error(f"Failed to load predictions: {e}")
        sys.exit(1)

    # Run analysis
    results = run_sensitivity_analysis(
        predictions,
        true_values,
        sweep_factor=args.sweep_factor,
        num_points=args.num_points
    )

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['threshold', 'fpr', 'fnr', 'sweep_factor']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Sensitivity analysis complete. Results written to {output_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()