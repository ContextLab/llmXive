"""
Sensitivity Analysis for Material Strength Prediction.

Implements FR-007: Binarize using median predicted strength of the test set.
Sweep thresholds across median ± 5%, median ± 10%, median ± 20%.
Compute FPR (False Positive Rate) and FNR (False Negative Rate).

Output: results/sensitivity_analysis.csv with columns: threshold, fpr, fnr.
"""

import os
import sys
import json
import logging
import argparse
import csv
import math
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# Import from project utils (API surface provided)
from utils.config import get_project_root, get_results_dir, get_data_dir, set_seed, get_seed

# Setup logging
def setup_logging() -> logging.Logger:
    """Initialize logger for sensitivity analysis."""
    logger = logging.getLogger("sensitivity")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

logger = setup_logging()

def load_predictions(predictions_path: Path) -> Tuple[List[float], List[float]]:
    """
    Load predictions and true values from a CSV file.
    Expects columns: 'predicted_strength', 'true_strength' (or similar).
    Returns: (predicted_values, true_values)
    """
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")

    predicted = []
    true_vals = []

    with open(predictions_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        # Handle potential column name variations
        pred_col = None
        true_col = None
        for field in reader.fieldnames or []:
            if 'predicted' in field.lower() or 'pred' in field.lower():
                pred_col = field
            if 'true' in field.lower() or 'actual' in field.lower() or 'label' in field.lower():
                true_col = field

        if not pred_col or not true_col:
            raise ValueError(f"Could not find prediction/true columns in {predictions_path}. Fields: {reader.fieldnames}")

        for row in reader:
            try:
                predicted.append(float(row[pred_col]))
                true_vals.append(float(row[true_col]))
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping row due to invalid data: {e}")
                continue

    if len(predicted) == 0:
        raise ValueError("No valid data found in predictions file.")

    return predicted, true_vals

def binarize_by_median(
    predictions: List[float],
    true_values: List[float],
    offset_percentages: List[float]
) -> List[Dict[str, float]]:
    """
    Binarize using the median of predicted strengths.
    Sweep thresholds: median * (1 + offset) for offset in offset_percentages.
    Compute FPR and FNR for each threshold.

    Logic:
    - Positive Class: True Strength >= Median Predicted (or similar logic).
      However, standard sensitivity analysis usually sweeps a threshold on the PREDICTED score
      against a fixed binary ground truth. Here, the spec says "Binarize using median predicted strength".
      Interpretation: We treat the task as a binary classification where the threshold
      determines the cut-off for "High Strength".
      - If Predicted >= Threshold -> Predicted Positive.
      - If True >= Median Predicted -> Actual Positive (Ground Truth derived from median of predictions for consistency).
      OR more likely: The ground truth is the continuous value, and we are evaluating
      the sensitivity of a binary decision boundary.
      Standard approach:
      1. Calculate Median of Predicted Values (M).
      2. Define Thresholds T = M * (1 + k) for k in [-0.2, -0.1, -0.05, 0.05, 0.1, 0.2].
      3. For each T:
         - Predicted Positive if Predicted >= T.
         - Actual Positive if True >= M (The median of the predictions serves as the reference point for "High Strength" in the absence of a hard physical threshold, or we assume the ground truth is binarized at the median of the distribution).
         *Refinement based on Spec US-3 Scenario 2*: "Binarize using median predicted strength".
         This implies the ground truth is binarized at the median of the predictions (or the median of the true values if they are aligned).
         Let's assume the "True" label is 1 if True_Strength >= Median_Predicted, else 0.
         Then we sweep the decision threshold on the Prediction.

    Returns: List of dicts {threshold, fpr, fnr}
    """
    if len(predictions) != len(true_values):
        raise ValueError("Predictions and true values must have the same length.")

    # Calculate median of predictions
    sorted_preds = sorted(predictions)
    n = len(sorted_preds)
    if n % 2 == 0:
        median_pred = (sorted_preds[n // 2 - 1] + sorted_preds[n // 2]) / 2
    else:
        median_pred = sorted_preds[n // 2]

    logger.info(f"Calculated median predicted strength: {median_pred:.4f}")

    # Define thresholds: median * (1 + offset)
    # Offsets: -20%, -10%, -5%, +5%, +10%, +20%
    thresholds = []
    for offset in offset_percentages:
        threshold = median_pred * (1.0 + offset)
        thresholds.append(threshold)

    # Sort thresholds for logging
    thresholds.sort()

    results = []
    # Binarize Ground Truth based on Median Predicted (Scenario 2 interpretation)
    # True Positive if True_Strength >= median_pred
    actual_labels = [1 if t >= median_pred else 0 for t in true_values]

    for thresh in thresholds:
        # Predictions: 1 if pred >= thresh
        pred_labels = [1 if p >= thresh else 0 for p in predictions]

        # Confusion Matrix
        tp = sum(1 for a, p in zip(actual_labels, pred_labels) if a == 1 and p == 1)
        fp = sum(1 for a, p in zip(actual_labels, pred_labels) if a == 0 and p == 1)
        tn = sum(1 for a, p in zip(actual_labels, pred_labels) if a == 0 and p == 0)
        fn = sum(1 for a, p in zip(actual_labels, pred_labels) if a == 1 and p == 0)

        # FPR = FP / (FP + TN)
        # FNR = FN / (FN + TP)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        results.append({
            "threshold": thresh,
            "fpr": fpr,
            "fnr": fnr,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn
        })

        logger.debug(f"Threshold {thresh:.4f}: TP={tp}, FP={fp}, TN={tn}, FN={fn}, FPR={fpr:.4f}, FNR={fnr:.4f}")

    return results

def compute_fpr_fnr(
    predictions: List[float],
    true_values: List[float],
    threshold: float
) -> Tuple[float, float]:
    """
    Helper to compute FPR and FNR for a single threshold.
    Used if we need to call this function externally.
    """
    # Binarize ground truth at median of predictions (consistent with run_sensitivity_analysis)
    sorted_preds = sorted(predictions)
    n = len(sorted_preds)
    median_pred = sorted_preds[n // 2] if n % 2 else (sorted_preds[n // 2 - 1] + sorted_preds[n // 2]) / 2
    
    actual_labels = [1 if t >= median_pred else 0 for t in true_values]
    pred_labels = [1 if p >= threshold else 0 for p in predictions]

    tp = sum(1 for a, p in zip(actual_labels, pred_labels) if a == 1 and p == 1)
    fp = sum(1 for a, p in zip(actual_labels, pred_labels) if a == 0 and p == 1)
    tn = sum(1 for a, p in zip(actual_labels, pred_labels) if a == 0 and p == 0)
    fn = sum(1 for a, p in zip(actual_labels, pred_labels) if a == 1 and p == 0)

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    return fpr, fnr

def run_sensitivity_analysis(
    predictions_path: Path,
    output_path: Path,
    offsets: Optional[List[float]] = None
) -> Path:
    """
    Main orchestration function for sensitivity analysis.
    Loads predictions, computes FPR/FNR across thresholds, writes CSV.
    """
    logger.info(f"Loading predictions from: {predictions_path}")
    predictions, true_values = load_predictions(predictions_path)
    logger.info(f"Loaded {len(predictions)} samples.")

    if offsets is None:
        offsets = [-0.20, -0.10, -0.05, 0.05, 0.10, 0.20]

    logger.info(f"Running sensitivity analysis with offsets: {offsets}")
    results = binarize_by_median(predictions, true_values, offsets)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['threshold', 'fpr', 'fnr', 'tp', 'fp', 'tn', 'fn'])
        writer.writeheader()
        for row in results:
            # Write only required columns for the artifact, or all for debugging?
            # Spec: "Output: results/sensitivity_analysis.csv with columns threshold, fpr, fnr"
            writer.writerow({
                'threshold': row['threshold'],
                'fpr': row['fpr'],
                'fnr': row['fnr'],
                'tp': row['tp'],
                'fp': row['fp'],
                'tn': row['tn'],
                'fn': row['fn']
            })

    logger.info(f"Sensitivity analysis complete. Output written to: {output_path}")
    return output_path

def main():
    """CLI Entry point."""
    parser = argparse.ArgumentParser(description="Run Sensitivity Analysis on Material Strength Predictions")
    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Path to CSV file with predictions (e.g., results/predictions.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output CSV (default: results/sensitivity_analysis.csv)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed (optional)"
    )

    args = parser.parse_args()

    if args.seed is not None:
        set_seed(args.seed)
        logger.info(f"Seed set to: {args.seed}")

    project_root = get_project_root()
    predictions_path = Path(args.predictions)
    if not predictions_path.is_absolute():
        predictions_path = project_root / predictions_path

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = project_root / output_path
    else:
        output_path = get_results_dir() / "sensitivity_analysis.csv"

    try:
        run_sensitivity_analysis(predictions_path, output_path)
        logger.info("Analysis completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()