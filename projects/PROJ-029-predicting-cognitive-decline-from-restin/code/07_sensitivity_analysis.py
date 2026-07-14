"""
code/07_sensitivity_analysis.py
Implements T030a: Decision threshold sweep analysis on the trained model.
"""
import os
import sys
import json
import argparse
import warnings
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import confusion_matrix, roc_auc_score

# Project imports
from utils.logger import get_logger
from utils.io import ensure_dir, load_csv, load_json

# --- Configuration ---
THRESHOLDS = [0.45, 0.50, 0.55]
MODEL_PATH = Path("data/processed/model.pkl")
DATA_PATH = Path("data/processed/graph_metrics.csv")
LABEL_COLUMN = "decline_label"  # Expected column in graph_metrics.csv
OUTPUT_PATH = Path("data/processed/sensitivity_report.json")

# --- Logger Setup ---
def get_logger_wrapper():
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = get_logger_wrapper()

# --- Core Logic ---
def calculate_fpr_fnr(y_true, y_prob, threshold):
    """
    Calculate False Positive Rate (FPR) and False Negative Rate (FNR)
    for a given probability threshold.

    Definitions:
    - Positive class: Decline (Label = 1)
    - Negative class: No Decline (Label = 0)

    Threshold logic:
    - Predicted Positive (Decline) if y_prob >= threshold
    - Predicted Negative (No Decline) if y_prob < threshold

    FPR = FP / (FP + TN)  (False alarms among healthy)
    FNR = FN / (FN + TP)  (Missed cases among sick)
    """
    y_pred = (y_prob >= threshold).astype(int)

    # True Positives, True Negatives, False Positives, False Negatives
    tp = np.sum((y_pred == 1) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))

    # Calculate rates, handling division by zero
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    return {
        "threshold": float(threshold),
        "fpr": float(fpr),
        "fnr": float(fnr),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "total_positive": int(tp + fn),
        "total_negative": int(tn + fp)
    }

def load_model_and_data():
    """
    Load the trained Random Forest model and the graph metrics dataset.
    """
    if not MODEL_PATH.exists():
        logger.error(f"Model file not found: {MODEL_PATH}")
        logger.error("Please run code/04_train_model.py first.")
        sys.exit(1)

    if not DATA_PATH.exists():
        logger.error(f"Data file not found: {DATA_PATH}")
        logger.error("Please run code/03_compute_graph_metrics.py first.")
        sys.exit(1)

    try:
        model = joblib.load(MODEL_PATH)
        logger.info(f"Model loaded successfully from {MODEL_PATH}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    try:
        df = load_csv(DATA_PATH)
        logger.info(f"Data loaded successfully from {DATA_PATH} ({len(df)} rows)")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    if LABEL_COLUMN not in df.columns:
        logger.error(f"Label column '{LABEL_COLUMN}' not found in data.")
        logger.error(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    # Identify feature columns (all except subject_id, label, and non-numeric)
    # Assuming graph_metrics.csv has a 'subject_id' and the label column,
    # and the rest are numeric features.
    feature_cols = [col for col in df.columns if col not in ['subject_id', LABEL_COLUMN] and np.issubdtype(df[col].dtype, np.number)]
    
    if not feature_cols:
        logger.error("No feature columns found in the dataset.")
        sys.exit(1)

    X = df[feature_cols].values
    y = df[LABEL_COLUMN].values

    # Check for NaNs in features
    if np.isnan(X).any():
        logger.warning("NaN values detected in features. Dropping rows with NaNs.")
        mask = ~np.isnan(X).any(axis=1)
        X = X[mask]
        y = y[mask]

    return model, X, y

def run_threshold_sweep(model, X, y):
    """
    Run the decision threshold sweep over the predefined thresholds.
    """
    logger.info(f"Starting threshold sweep over {THRESHOLDS}...")
    
    # Get predicted probabilities for the positive class (class 1)
    if hasattr(model, 'predict_proba'):
        y_prob = model.predict_proba(X)[:, 1]
    else:
        logger.error("Model does not support predict_proba. Cannot run threshold sweep.")
        sys.exit(1)

    results = []
    for thresh in THRESHOLDS:
        logger.info(f"Calculating metrics for threshold = {thresh}")
        metrics = calculate_fpr_fnr(y, y_prob, thresh)
        results.append(metrics)
        logger.info(f"  FPR: {metrics['fpr']:.4f}, FNR: {metrics['fnr']:.4f}")

    return results


def write_outputs(results: Dict[str, Any]) -> None:
    """Write results to JSON file."""
    ensure_dir(OUTPUT_PATH.parent)
    save_json(OUTPUT_PATH, results)
    logger.info(f"Sensitivity report written to {OUTPUT_PATH}")


def main():
    logger.info("Starting Sensitivity Analysis (Part 1: Threshold Sweep)")
    
    # Load data and model
    model, X, y = load_model_and_data()
    
    # Run sweep
    results = run_threshold_sweep(model, X, y)
    
    # Prepare output
    output_data = {
        "analysis_type": "decision_threshold_sweep",
        "thresholds_tested": THRESHOLDS,
        "results": results,
        "model_path": str(MODEL_PATH),
        "data_path": str(DATA_PATH),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Write output
    ensure_dir(OUTPUT_PATH)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Sensitivity report written to {OUTPUT_PATH}")
    logger.info("Threshold sweep completed successfully.")


if __name__ == "__main__":
    main()