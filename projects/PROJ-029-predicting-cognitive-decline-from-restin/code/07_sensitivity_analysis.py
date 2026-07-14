"""
T030a: Sensitivity Analysis (Part 1) - Decision Threshold Sweep
Performs a decision threshold sweep over {0.45, 0.50, 0.55} on the trained model.
Reports false-positive and false-negative rates for each threshold.
"""
import os
import sys
import json
import argparse
import warnings
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
import joblib

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.io import load_json, save_json, load_csv, save_csv, ensure_dir
from config import get_config

# Configure logger
logger = get_logger("sensitivity_analysis")

# Constants
THRESHOLDS = [0.45, 0.50, 0.55]
DEFAULT_MODEL_PATH = "data/processed/model.pkl"
DEFAULT_METRICS_PATH = "data/processed/graph_metrics.csv"
DEFAULT_OUTPUT_PATH = "data/processed/sensitivity_report.json"
DEFAULT_DATA_SPLIT_PATH = "data/processed/data_split_indices.json"

def load_model_and_data(
    model_path: str,
    metrics_path: str,
    split_path: Optional[str] = None
) -> Tuple[Any, pd.DataFrame, Dict[str, List[int]]]:
    """
    Load the trained model, graph metrics data, and data split indices.

    Args:
        model_path: Path to the serialized model (pkl)
        metrics_path: Path to the graph metrics CSV
        split_path: Path to the data split indices JSON

    Returns:
        Tuple of (model, metrics_df, split_indices)
    """
    logger.info(f"Loading model from {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    model = joblib.load(model_path)

    logger.info(f"Loading graph metrics from {metrics_path}")
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    metrics_df = load_csv(metrics_path)

    # Ensure we have the necessary columns
    required_cols = ['subject_id', 'decline_label']
    for col in required_cols:
        if col not in metrics_df.columns:
            raise ValueError(f"Missing required column in metrics: {col}")

    # Load split indices if available, otherwise create a default split
    split_indices = {}
    if split_path and os.path.exists(split_path):
        logger.info(f"Loading data split indices from {split_path}")
        split_indices = load_json(split_path)
    else:
        logger.warning(f"Split indices not found at {split_path}. "
                       "Creating a default 80/20 split for evaluation.")
        # Create a deterministic split based on subject count
        n = len(metrics_df)
        indices = list(range(n))
        split_point = int(n * 0.8)
        split_indices = {
            "train": indices[:split_point],
            "test": indices[split_point:]
        }

    return model, metrics_df, split_indices

def calculate_fpr_fnr(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float
) -> Tuple[float, float]:
    """
    Calculate False Positive Rate and False Negative Rate for a given threshold.

    Args:
        y_true: True labels (0 or 1)
        y_prob: Predicted probabilities of positive class
        threshold: Decision threshold

    Returns:
        Tuple of (FPR, FNR)
    """
    y_pred = (y_prob >= threshold).astype(int)

    # True Positives, False Positives, True Negatives, False Negatives
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))

    # Calculate rates
    # FPR = FP / (FP + TN)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    # FNR = FN / (FN + TP)
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    return fpr, fnr

def run_sensitivity_analysis(
    model: Any,
    metrics_df: pd.DataFrame,
    split_indices: Dict[str, List[int]],
    thresholds: List[float] = THRESHOLDS
) -> Dict[str, Any]:
    """
    Run sensitivity analysis by evaluating the model at different decision thresholds.

    Args:
        model: Trained model object
        metrics_df: DataFrame containing features and labels
        split_indices: Dictionary with 'test' key containing indices for test set
        thresholds: List of thresholds to evaluate

    Returns:
        Dictionary containing analysis results
    """
    # Extract test set data
    test_indices = split_indices.get("test", [])
    if not test_indices:
        logger.warning("No test indices found. Using all data for evaluation.")
        test_indices = list(range(len(metrics_df)))

    # Prepare features and labels for test set
    # Exclude non-feature columns
    feature_cols = [col for col in metrics_df.columns 
                    if col not in ['subject_id', 'decline_label']]
    
    X_test = metrics_df.loc[test_indices, feature_cols].values
    y_true = metrics_df.loc[test_indices, 'decline_label'].values

    # Get predicted probabilities from the model
    # Assuming the model has predict_proba method (Random Forest, etc.)
    if hasattr(model, 'predict_proba'):
        y_prob = model.predict_proba(X_test)[:, 1]
    elif hasattr(model, 'predict'):
        # If only predict is available, we cannot get probabilities
        # We will use the predictions directly and set probabilities to 0.5 for thresholding
        logger.warning("Model does not have predict_proba. Using predictions directly. "
                       "Threshold sweep may not be meaningful.")
        y_pred_direct = model.predict(X_test)
        # Fallback: treat all as 0.5 probability for thresholding purposes
        # This is a limitation if the model doesn't support probabilities
        y_prob = np.full_like(y_pred_direct, 0.5, dtype=float)
    else:
        raise ValueError("Model must have predict_proba or predict method.")

    results = {
        "thresholds": thresholds,
        "evaluations": []
    }

    for thresh in thresholds:
        fpr, fnr = calculate_fpr_fnr(y_true, y_prob, thresh)
        
        # Additional metrics for context
        y_pred = (y_prob >= thresh).astype(int)
        accuracy = np.mean(y_pred == y_true)
        precision = np.sum((y_pred == 1) & (y_true == 1)) / np.sum(y_pred == 1) if np.sum(y_pred == 1) > 0 else 0.0
        recall = np.sum((y_pred == 1) & (y_true == 1)) / np.sum(y_true == 1) if np.sum(y_true == 1) > 0 else 0.0

        results["evaluations"].append({
            "threshold": thresh,
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "num_test_samples": len(y_true)
        })
        logger.info(f"Threshold {thresh}: FPR={fpr:.4f}, FNR={fnr:.4f}, Acc={accuracy:.4f}")

    return results

def write_outputs(results: Dict[str, Any], output_path: str) -> None:
    """
    Write sensitivity analysis results to JSON file.

    Args:
        results: Analysis results dictionary
        output_path: Path to output JSON file
    """
    ensure_dir(output_path)
    save_json(results, output_path)
    logger.info(f"Sensitivity analysis results written to {output_path}")

def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(description="Sensitivity Analysis (Threshold Sweep)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_PATH,
                        help="Path to trained model file")
    parser.add_argument("--metrics", type=str, default=DEFAULT_METRICS_PATH,
                        help="Path to graph metrics CSV")
    parser.add_argument("--split", type=str, default=DEFAULT_DATA_SPLIT_PATH,
                        help="Path to data split indices JSON")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_PATH,
                        help="Path to output JSON file")
    
    args = parser.parse_args()

    logger.info("Starting T030a: Sensitivity Analysis (Part 1)")
    logger.info(f"Thresholds to evaluate: {THRESHOLDS}")

    try:
        # Load model and data
        model, metrics_df, split_indices = load_model_and_data(
            args.model, args.metrics, args.split
        )

        # Run sensitivity analysis
        results = run_sensitivity_analysis(model, metrics_df, split_indices, THRESHOLDS)

        # Write outputs
        write_outputs(results, args.output)

        logger.info("T030a completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Please ensure the model and metrics files exist.")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())