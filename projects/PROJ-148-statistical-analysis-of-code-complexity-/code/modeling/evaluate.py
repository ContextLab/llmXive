from __future__ import annotations

import argparse
import json
import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    calibration_curve,
    roc_curve,
    precision_recall_curve,
    log_loss,
)
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

from utils.logging import get_logger
from utils.config import get_seed

# Configure logging
logger = get_logger(__name__)

# Constants
DATA_DIR = Path("data")
MODEL_DIR = Path("data/model")
FIGURES_DIR = Path("figures")

# Ensure directories exist
MODEL_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def load_test_data() -> Tuple[np.ndarray, np.ndarray, list]:
    """
    Load the test dataset from data/test_data.csv.
    Returns X (features), y (labels), and feature_names (list).
    """
    test_path = DATA_DIR / "test_data.csv"
    if not test_path.exists():
        raise FileNotFoundError(
            f"Test data file not found at {test_path}. "
            "Please run the data pipeline first (data pipeline tasks)."
        )

    df = pd.read_csv(test_path)

    # Identify target column
    if "bug_label" not in df.columns:
        raise ValueError("Test data must contain a 'bug_label' column.")

    # Separate features and target
    y = df["bug_label"].values
    feature_cols = [col for col in df.columns if col != "bug_label"]
    X = df[feature_cols].values
    feature_names = feature_cols

    logger.info(f"Loaded test data: {X.shape[0]} samples, {X.shape[1]} features.")
    return X, y, feature_names

def load_model(model_name: str) -> Any:
    """
    Load a trained model from data/model/{model_name}.pkl.
    """
    model_path = MODEL_DIR / f"{model_name}.pkl"
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found at {model_path}. "
            "Please train the model first."
        )
    return joblib.load(model_path)

def compute_metrics(
    y_true: np.ndarray, y_prob: np.ndarray, model_name: str
) -> Dict[str, float]:
    """
    Compute ROC-AUC, PR-AUC, and Log-Loss.
    Asserts ROC-AUC >= 0.50 baseline.
    """
    roc_auc = roc_auc_score(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)
    log_loss_val = log_loss(y_true, y_prob)

    logger.info(f"Model {model_name} ROC-AUC: {roc_auc:.4f}")
    logger.info(f"Model {model_name} PR-AUC: {pr_auc:.4f}")
    logger.info(f"Model {model_name} Log-Loss: {log_loss_val:.4f}")

    # Baseline assertion
    if roc_auc < 0.50:
        raise AssertionError(
            f"Model {model_name} ROC-AUC ({roc_auc:.4f}) is below the 0.50 baseline. "
            "The model is performing worse than random guessing."
        )

    return {
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "log_loss": log_loss_val,
    }

def plot_calibration(
    y_true: np.ndarray, y_prob: np.ndarray, model_name: str
) -> str:
    """
    Generate a calibration plot and save it to figures/calibration_{model_name}.png.
    Returns the path to the saved figure.
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    # Calculate calibration curve
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)

    # Plot perfectly calibrated line
    ax.plot([0, 1], [0, 1], "k--", label="Ideally calibrated")

    # Plot actual calibration
    ax.plot(prob_pred, prob_true, marker="o", label=f"{model_name}")

    ax.set_xlabel("Mean Predicted Probability")
    ax.set_ylabel("Fraction of Positives")
    ax.set_title(f"Calibration Plot: {model_name}")
    ax.legend(loc="lower right")
    ax.grid(True)

    # Save figure
    out_path = FIGURES_DIR / f"calibration_{model_name}.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    logger.info(f"Calibration plot saved to {out_path}")
    return str(out_path)

def plot_roc_curve(
    y_true: np.ndarray, y_prob: np.ndarray, model_name: str
) -> str:
    """
    Generate an ROC curve and save it to figures/roc_{model_name}.png.
    Returns the path to the saved figure.
    """
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = roc_auc_score(y_true, y_prob)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {roc_auc:.2f})")
    ax.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--", label="Random")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(f"Receiver Operating Characteristic: {model_name}")
    ax.legend(loc="lower right")
    ax.grid(True)

    out_path = FIGURES_DIR / f"roc_{model_name}.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    logger.info(f"ROC curve saved to {out_path}")
    return str(out_path)

def plot_pr_curve(
    y_true: np.ndarray, y_prob: np.ndarray, model_name: str
) -> str:
    """
    Generate a Precision-Recall curve and save it to figures/pr_{model_name}.png.
    Returns the path to the saved figure.
    """
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(recall, precision, color="blue", lw=2, label=f"PR curve (AUC = {pr_auc:.2f})")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(f"Precision-Recall Curve: {model_name}")
    ax.legend(loc="lower left")
    ax.grid(True)

    out_path = FIGURES_DIR / f"pr_{model_name}.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    logger.info(f"PR curve saved to {out_path}")
    return str(out_path)

def evaluate_model(model_name: str) -> Tuple[Dict[str, float], str, str, str]:
    """
    Main evaluation function for a specific model.
    Loads data, loads model, computes metrics, and generates plots.
    Returns (metrics_dict, cal_path, roc_path, pr_path).
    """
    logger.info(f"Starting evaluation for model: {model_name}")

    # Load data
    X, y, feature_names = load_test_data()

    # Load model
    model = load_model(model_name)

    # Predict probabilities
    # Handle both sklearn models (predict_proba) and potential custom wrappers
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X)[:, 1]
    else:
        raise AttributeError(f"Model {model_name} does not have predict_proba method.")

    # Compute metrics
    metrics = compute_metrics(y, y_prob, model_name)

    # Generate plots
    cal_path = plot_calibration(y, y_prob, model_name)
    roc_path = plot_roc_curve(y, y_prob, model_name)
    pr_path = plot_pr_curve(y, y_prob, model_name)

    # Save metrics to JSON
    metrics_path = MODEL_DIR / f"metrics_{model_name}.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    return metrics, cal_path, roc_path, pr_path

def main():
    """
    Entry point for the evaluation script.
    Expects --model argument to specify which model to evaluate.
    """
    parser = argparse.ArgumentParser(
        description="Evaluate model performance (ROC-AUC, PR-AUC, Calibration)."
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        choices=["primary", "alternative"],
        help="Name of the model to evaluate ('primary' or 'alternative').",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )

    args = parser.parse_args()

    # Set seed
    from utils.config import set_random_seed
    set_random_seed(args.seed)

    try:
        metrics, cal_path, roc_path, pr_path = evaluate_model(args.model)
        logger.info(f"Evaluation completed successfully for {args.model}.")
        logger.info(f"Metrics: {metrics}")
        logger.info(f"Plots: Calibration={cal_path}, ROC={roc_path}, PR={pr_path}")
    except FileNotFoundError as e:
        logger.error(f"Data or Model file not found: {e}")
        sys.exit(1)
    except AssertionError as e:
        logger.error(f"Baseline assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    main()