"""
code/07_sensitivity_analysis.py (Part 1)

Implements decision threshold sweep over {0.45, 0.50, 0.55} on the trained model.
Reports false-positive/false-negative rates for each threshold.

This script assumes a pre-trained model exists at `data/processed/model.pkl`
and corresponding feature data at `data/processed/graph_metrics.csv`.
"""

import os
import sys
import json
import argparse
import warnings
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import confusion_matrix, roc_auc_score

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.io import load_csv, save_json

# Constants
MODEL_PATH = project_root / "data" / "processed" / "model.pkl"
DATA_PATH = project_root / "data" / "processed" / "graph_metrics.csv"
ELIGIBLE_PATH = project_root / "data" / "processed" / "eligible_subjects.csv"
OUTPUT_PATH = project_root / "data" / "processed" / "sensitivity_report.json"

THRESHOLDS = [0.45, 0.50, 0.55]
DECLINE_LABEL_COL = "decline_label"  # Assuming this column exists in graph_metrics or derived

logger = get_logger(__name__)


def load_model_and_data() -> Tuple[Any, pd.DataFrame, pd.DataFrame]:
    """Load the trained model and required data."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}. Run T023 first.")
    
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}. Run T019 first.")

    logger.info(f"Loading model from {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)

    logger.info(f"Loading data from {DATA_PATH}")
    df = load_csv(DATA_PATH)

    # Ensure we have the label column
    if DECLINE_LABEL_COL not in df.columns:
        raise ValueError(f"Required column '{DECLINE_LABEL_COL}' not found in {DATA_PATH}")

    # Separate features and target
    # Assuming all columns except subject_id and decline_label are features
    feature_cols = [c for c in df.columns if c not in ['subject_id', DECLINE_LABEL_COL]]
    if not feature_cols:
        raise ValueError("No feature columns found in data.")

    X = df[feature_cols].values
    y = df[DECLINE_LABEL_COL].values

    return model, X, y, feature_cols


def calculate_threshold_metrics(
    model: Any, 
    X: np.ndarray, 
    y: np.ndarray, 
    threshold: float
) -> Dict[str, Any]:
    """
    Calculate FP and FN rates for a specific decision threshold.
    
    Returns:
        Dictionary with threshold, fp_rate, fn_rate, tn, fp, fn, tn.
    """
    # Get prediction probabilities for the positive class
    if hasattr(model, 'predict_proba'):
        probas = model.predict_proba(X)[:, 1]
    else:
        # Fallback if model only has predict (should not happen for RF)
        logger.warning("Model does not support predict_proba. Using predict.")
        # This is a degenerate case for threshold sweep, but handle gracefully
        preds = model.predict(X)
        # Map 0->0.0, 1->1.0 for thresholding
        probas = preds.astype(float)

    # Apply threshold
    y_pred = (probas >= threshold).astype(int)

    # Calculate confusion matrix: TN, FP, FN, TP
    # confusion_matrix returns: [[TN, FP], [FN, TP]]
    tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()

    total_neg = tn + fp
    total_pos = fn + tp

    fp_rate = fp / total_neg if total_neg > 0 else 0.0
    fn_rate = fn / total_pos if total_pos > 0 else 0.0

    return {
        "threshold": float(threshold),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "fp_rate": float(fp_rate),
        "fn_rate": float(fn_rate)
    }


def run_sensitivity_analysis() -> Dict[str, Any]:
    """
    Perform the threshold sweep analysis.
    
    Returns:
        Dictionary containing results for all thresholds.
    """
    logger.info("Loading model and data...")
    try:
        model, X, y, feature_cols = load_model_and_data()
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        raise

    logger.info(f"Loaded {len(y)} samples with {len(feature_cols)} features.")
    
    results = {
        "analysis_type": "decision_threshold_sweep",
        "thresholds_tested": THRESHOLDS,
        "feature_columns": feature_cols,
        "total_samples": int(len(y)),
        "positive_samples": int(np.sum(y)),
        "negative_samples": int(len(y) - np.sum(y)),
        "threshold_results": []
    }

    for thresh in THRESHOLDS:
        logger.info(f"Calculating metrics for threshold = {thresh}")
        metrics = calculate_threshold_metrics(model, X, y, thresh)
        results["threshold_results"].append(metrics)
        logger.info(
            f"  Threshold {thresh}: FP Rate = {metrics['fp_rate']:.4f}, "
            f"FN Rate = {metrics['fn_rate']:.4f}"
        )

    return results


def write_outputs(results: Dict[str, Any]) -> None:
    """Write results to JSON file."""
    ensure_dir(OUTPUT_PATH.parent)
    save_json(OUTPUT_PATH, results)
    logger.info(f"Sensitivity report written to {OUTPUT_PATH}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Sensitivity Analysis (Part 1: Threshold Sweep)")
    parser.add_argument("--thresholds", type=str, default="0.45,0.50,0.55",
                        help="Comma-separated list of thresholds to test")
    args = parser.parse_args()

    # Override thresholds if provided
    global THRESHOLDS
    THRESHOLDS = [float(t) for t in args.thresholds.split(",")]

    logger.info("Starting Sensitivity Analysis (Part 1: Threshold Sweep)")
    
    try:
        results = run_sensitivity_analysis()
        write_outputs(results)
        logger.info("Sensitivity Analysis completed successfully.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()