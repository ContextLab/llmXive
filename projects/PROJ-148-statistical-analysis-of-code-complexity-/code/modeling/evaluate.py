from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    roc_curve,
    precision_recall_curve,
    brier_score_loss,
)
from sklearn.calibration import calibration_curve
from pathlib import Path
from typing import Dict, Tuple, Optional

# Import local project utilities
from utils.logging import get_logger
from utils.config import get_seed

logger = get_logger(__name__)


def load_test_data(data_dir: Path) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Load the preprocessed test data from the data directory.
    Expects a file named 'test_data.csv' in the data directory.
    """
    test_path = data_dir / "test_data.csv"
    if not test_path.exists():
        raise FileNotFoundError(f"Test data file not found at {test_path}. "
                                "Ensure the data pipeline has been run successfully.")

    df = pd.read_csv(test_path)

    # Expected columns based on previous pipeline steps
    # We assume 'bug_label' is the target and others are features
    target_col = "bug_label"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in {test_path}. "
                         f"Available columns: {df.columns.tolist()}")

    y_true = df[target_col].values
    # Features are all numeric columns except the target
    feature_cols = [col for col in df.columns if col != target_col and df[col].dtype in ['int64', 'float64']]
    X = df[feature_cols].values

    logger.info(f"Loaded test data: {len(y_true)} samples, {len(feature_cols)} features.")
    return df, X, y_true


def load_model(model_path: Path):
    """Load a trained model from disk."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    return joblib.load(model_path)


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """
    Compute ROC-AUC, PR-AUC, and Brier score.
    Asserts ROC-AUC >= 0.50 baseline.
    """
    roc_auc = roc_auc_score(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)
    brier = brier_score_loss(y_true, y_prob)

    logger.info(f"ROC-AUC: {roc_auc:.4f}, PR-AUC: {pr_auc:.4f}, Brier Score: {brier:.4f}")

    # Assertion for baseline requirement
    if roc_auc < 0.50:
        raise ValueError(
            f"Model performance below baseline! ROC-AUC ({roc_auc:.4f}) < 0.50. "
            "The model is performing worse than random guessing."
        )

    return {
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "brier_score": float(brier),
        "baseline_met": roc_auc >= 0.50
    }


def plot_roc_curve(y_true: np.ndarray, y_prob: np.ndarray, output_path: Path):
    """Generate and save the ROC curve plot."""
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc_score(y_true, y_prob):.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Guess')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.legend(loc="lower right")
    plt.grid(True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"ROC curve saved to {output_path}")


def plot_pr_curve(y_true: np.ndarray, y_prob: np.ndarray, output_path: Path):
    """Generate and save the Precision-Recall curve plot."""
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, color='blue', lw=2, label=f'PR curve (AP = {average_precision_score(y_true, y_prob):.2f})')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend(loc="lower left")
    plt.grid(True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"PR curve saved to {output_path}")


def plot_calibration(y_true: np.ndarray, y_prob: np.ndarray, output_path: Path, n_bins: int = 10):
    """Generate and save the calibration plot."""
    # calibration_curve expects 1D array
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins)

    plt.figure(figsize=(8, 6))
    plt.plot(prob_pred, prob_true, marker='o', ms=5, label='Model', color='blue')
    plt.plot([0, 1], [0, 1], linestyle='--', label='Perfectly Calibrated', color='gray')
    plt.xlabel('Mean Predicted Probability')
    plt.ylabel('Fraction of Positives')
    plt.title('Calibration Plot (Reliability Curve)')
    plt.legend(loc="upper left")
    plt.grid(True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Calibration plot saved to {output_path}")


def evaluate_model(model, X: np.ndarray, y_true: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Run inference and compute metrics.
    Returns predicted probabilities and metrics dict.
    """
    y_prob = model.predict_proba(X)[:, 1]
    metrics = compute_metrics(y_true, y_prob)
    return y_prob, metrics


def save_metrics(metrics: Dict[str, float], output_path: Path):
    """Save evaluation metrics to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate the trained model on test data.")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to the directory containing test_data.csv")
    parser.add_argument("--model-path", type=str, required=True, help="Path to the trained model pickle file")
    parser.add_argument("--output-dir", type=str, required=True, help="Path to save plots and metrics")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    model_path = Path(args.model_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set random seed for reproducibility if needed
    set_random_seed(get_seed())

    # Load data and model
    logger.info("Loading test data...")
    df, X, y_true = load_test_data(data_dir)

    logger.info("Loading model...")
    model = load_model(model_path)

    # Evaluate
    logger.info("Evaluating model...")
    y_prob, metrics = evaluate_model(model, X, y_true)

    # Save metrics
    metrics_path = output_dir / "evaluation_metrics.json"
    save_metrics(metrics, metrics_path)

    # Generate plots
    roc_path = output_dir / "roc_curve.png"
    pr_path = output_dir / "pr_curve.png"
    cal_path = output_dir / "calibration_plot.png"

    plot_roc_curve(y_true, y_prob, roc_path)
    plot_pr_curve(y_true, y_prob, pr_path)
    plot_calibration(y_true, y_prob, cal_path)

    # Save a sample of probabilities for downstream tasks if needed
    # (e.g., for p-value correction or thresholds)
    prob_df = pd.DataFrame({"predicted_probability": y_prob, "true_label": y_true})
    prob_csv_path = output_dir / "test_predictions.csv"
    prob_df.to_csv(prob_csv_path, index=False)
    logger.info(f"Predictions saved to {prob_csv_path}")

    logger.info("Evaluation complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())