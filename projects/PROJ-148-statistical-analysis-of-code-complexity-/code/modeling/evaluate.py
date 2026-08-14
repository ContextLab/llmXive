from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional

import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    roc_auc_score,
    precision_recall_curve,
    auc,
    brier_score_loss,
    calibration_curve,
)
from sklearn.preprocessing import StandardScaler

# Import project utilities
from utils.logging import get_logger
from utils.config import get_seed, set_random_seed

logger = get_logger(__name__)


def load_test_data(data_dir: Path) -> Tuple[pd.DataFrame, pd.Series, list]:
    """
    Load the test split data from the data directory.
    Expects 'data/test_data.csv' to exist with columns matching the training data.
    Returns: (X_test_df, y_test_series, feature_names)
    """
    test_path = data_dir / "test_data.csv"
    if not test_path.exists():
        raise FileNotFoundError(f"Test data not found at {test_path}. "
                                "Ensure split_dataset.py has been run successfully.")

    df = pd.read_csv(test_path)
    # Identify target column
    if "bug_label" not in df.columns:
        raise ValueError("Target column 'bug_label' not found in test data.")

    y = df["bug_label"]
    # Features are all numeric columns excluding target and project_id if present
    feature_cols = [c for c in df.columns if c not in ["bug_label", "project_id", "file_id"]]
    X = df[feature_cols]

    # Drop rows with any NaN in features (should be handled by preprocess, but safe guard)
    mask = X.notna().all(axis=1)
    if not mask.all():
        logger.warning(f"Dropping { (~mask).sum() } rows with missing values in test data.")
        X = X[mask]
        y = y[mask]

    return X, y, feature_cols


def load_model(model_path: Path) -> object:
    """
    Load the trained model from the specified path.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    return joblib.load(model_path)


def compute_metrics(
    y_true: pd.Series,
    y_prob: np.ndarray,
    model_name: str = "Primary"
) -> Dict[str, float]:
    """
    Compute ROC-AUC, PR-AUC, and Brier score.
    """
    if len(np.unique(y_true)) < 2:
        logger.warning("Only one class present in y_true. Cannot compute ROC-AUC/PR-AUC.")
        return {
            "model_name": model_name,
            "roc_auc": np.nan,
            "pr_auc": np.nan,
            "brier_score": np.nan
        }

    roc_auc = roc_auc_score(y_true, y_prob)
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = auc(recall, precision)
    brier = brier_score_loss(y_true, y_prob)

    logger.info(f"{model_name} - ROC-AUC: {roc_auc:.4f}, PR-AUC: {pr_auc:.4f}, Brier: {brier:.4f}")

    return {
        "model_name": model_name,
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "brier_score": float(brier)
    }


def plot_roc_curve(
    y_true: pd.Series,
    y_prob: np.ndarray,
    model_name: str,
    output_path: Path
) -> None:
    """
    Plot ROC curve and save to file.
    """
    from sklearn.metrics import RocCurveDisplay

    plt.figure(figsize=(8, 6))
    RocCurveDisplay.from_predictions(y_true, y_prob, name=model_name)
    plt.plot([0, 1], [0, 1], "k--", label="Random")
    plt.title(f"ROC Curve - {model_name}")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved ROC curve to {output_path}")


def plot_pr_curve(
    y_true: pd.Series,
    y_prob: np.ndarray,
    model_name: str,
    output_path: Path
) -> None:
    """
    Plot Precision-Recall curve and save to file.
    """
    precision, recall, _ = precision_recall_curve(y_true, y_prob)

    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, label=model_name)
    plt.title(f"Precision-Recall Curve - {model_name}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved PR curve to {output_path}")


def plot_calibration(
    y_true: pd.Series,
    y_prob: np.ndarray,
    model_name: str,
    output_path: Path
) -> None:
    """
    Plot calibration curve and save to file.
    """
    plt.figure(figsize=(8, 6))
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)

    plt.plot(prob_pred, prob_true, marker="o", label=model_name, linewidth=2)
    plt.plot([0, 1], [0, 1], "k--", label="Perfect Calibration")
    plt.title(f"Calibration Curve - {model_name}")
    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Fraction of Positives")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved calibration curve to {output_path}")


def evaluate_model(
    model: object,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    output_dir: Path,
    model_name: str = "Primary"
) -> Dict[str, float]:
    """
    Evaluate the model on test data, compute metrics, and generate plots.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Predict probabilities
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)[:, 1]
    elif hasattr(model, "decision_function"):
        # For models without predict_proba (rare in sklearn for binary, but possible)
        y_prob = model.decision_function(X_test)
        # Normalize to [0,1] roughly for plotting if needed, but metrics handle raw scores
        # However, calibration_curve expects probabilities. Let's assume predict_proba path for now.
        raise ValueError("Model does not support predict_proba. Cannot compute calibration/PR-AUC properly.")
    else:
        raise AttributeError("Model has no predict_proba or decision_function method.")

    # Compute metrics
    metrics = compute_metrics(y_test, y_prob, model_name)

    # Generate plots
    plot_roc_curve(y_test, y_prob, model_name, output_dir / f"roc_{model_name.lower()}.png")
    plot_pr_curve(y_test, y_prob, model_name, output_dir / f"pr_{model_name.lower()}.png")
    plot_calibration(y_test, y_prob, model_name, output_dir / f"calibration_{model_name.lower()}.png")

    return metrics


def save_metrics(metrics: Dict[str, float], output_path: Path) -> None:
    """
    Save evaluation metrics to a JSON file.
    """
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {output_path}")


def main() -> None:
    """
    Main entry point for the evaluation script.
    """
    parser = argparse.ArgumentParser(description="Evaluate bug prediction model.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Path to the directory containing test_data.csv"
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        required=True,
        help="Path to the trained model pickle file"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Path to the directory where results and plots will be saved"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="Primary",
        help="Name of the model for reporting and plotting"
    )

    args = parser.parse_args()

    # Setup logging
    logger.info("Starting model evaluation...")

    # Load data
    try:
        X_test, y_test, feature_names = load_test_data(args.data_dir)
        logger.info(f"Loaded test data: {X_test.shape[0]} samples, {X_test.shape[1]} features")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Load model
    try:
        model = load_model(args.model_path)
        logger.info("Model loaded successfully")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Evaluate
    metrics = evaluate_model(
        model,
        X_test,
        y_test,
        args.output_dir,
        args.model_name
    )

    # Validate baseline
    if metrics["roc_auc"] < 0.50:
        logger.warning(f"ROC-AUC ({metrics['roc_auc']:.4f}) is below baseline (0.50).")
    else:
        logger.info(f"ROC-AUC ({metrics['roc_auc']:.4f}) meets baseline requirement (>= 0.50).")

    # Save metrics
    metrics_path = args.output_dir / "evaluation_metrics.json"
    save_metrics(metrics, metrics_path)

    logger.info("Evaluation complete.")


if __name__ == "__main__":
    main()