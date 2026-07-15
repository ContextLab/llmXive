"""
Evaluation module for statistical analysis of code complexity.

This module evaluates trained models on test data, computing ROC-AUC, PR-AUC,
and generating calibration plots. It asserts that the ROC-AUC meets the
required baseline of 0.50.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    roc_curve,
    precision_recall_curve,
    calibration_curve,
)
from sklearn.calibration import CalibratedClassifierCV

# Configure logging
logger = logging.getLogger(__name__)

# Ensure seaborn is available and set style
try:
    import seaborn as sns
    sns.set(style="whitegrid")
except ImportError:
    logger.error("Seaborn is required for plotting. Please install it.")
    raise

# Constants
BASELINE_ROC_AUC = 0.50
FIGURE_DPI = 300
FIGURE_SIZE = (10, 8)


def load_test_data(data_path: Path) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Load test data from a CSV file.

    Args:
        data_path: Path to the test data CSV file.

    Returns:
        Tuple of (DataFrame, features array, labels array).

    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If required columns are missing.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Test data file not found: {data_path}")

    df = pd.read_csv(data_path)

    # Ensure required columns exist
    required_cols = ["project_id", "bug_label"]
    # Feature columns are all numeric columns except bug_label and project_id
    # We assume the data has been preprocessed and cleaned
    feature_cols = [col for col in df.columns if col not in required_cols and df[col].dtype in [np.float64, np.int64]]

    if "bug_label" not in df.columns:
        raise ValueError(f"Missing required column 'bug_label' in {data_path}")

    if not feature_cols:
        raise ValueError(f"No feature columns found in {data_path}")

    X = df[feature_cols].values
    y = df["bug_label"].values

    logger.info(f"Loaded test data: {len(df)} samples, {len(feature_cols)} features")
    return df, X, y


def load_model(model_path: Path) -> Any:
    """
    Load a trained model from a pickle file.

    Args:
        model_path: Path to the model pickle file.

    Returns:
        The loaded model object.

    Raises:
        FileNotFoundError: If the model file does not exist.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = joblib.load(model_path)
    logger.info(f"Loaded model from {model_path}")
    return model


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """
    Compute evaluation metrics: ROC-AUC and PR-AUC.

    Args:
        y_true: True binary labels.
        y_prob: Predicted probabilities for the positive class.

    Returns:
        Dictionary containing ROC-AUC and PR-AUC scores.
    """
    if len(np.unique(y_true)) < 2:
        logger.warning("Only one class present in y_true. Returning NaN for metrics.")
        return {
            "roc_auc": float("nan"),
            "pr_auc": float("nan"),
        }

    roc_auc = roc_auc_score(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)

    logger.info(f"ROC-AUC: {roc_auc:.4f}, PR-AUC: {pr_auc:.4f}")
    return {
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
    }


def plot_roc_curve(y_true: np.ndarray, y_prob: np.ndarray, ax: Optional[plt.Axes] = None) -> plt.Axes:
    """
    Plot the Receiver Operating Characteristic (ROC) curve.

    Args:
        y_true: True binary labels.
        y_prob: Predicted probabilities for the positive class.
        ax: Matplotlib axes to plot on. If None, creates a new figure.

    Returns:
        The matplotlib axes object.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    roc_auc = roc_auc_score(y_true, y_prob)

    ax.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {roc_auc:.2f})")
    ax.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--", label="Random Classifier")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("Receiver Operating Characteristic (ROC) Curve")
    ax.legend(loc="lower right")
    ax.grid(True)

    return ax


def plot_pr_curve(y_true: np.ndarray, y_prob: np.ndarray, ax: Optional[plt.Axes] = None) -> plt.Axes:
    """
    Plot the Precision-Recall (PR) curve.

    Args:
        y_true: True binary labels.
        y_prob: Predicted probabilities for the positive class.
        ax: Matplotlib axes to plot on. If None, creates a new figure.

    Returns:
        The matplotlib axes object.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)

    ax.plot(recall, precision, color="blue", lw=2, label=f"PR curve (AUC = {pr_auc:.2f})")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall Curve")
    ax.legend(loc="lower left")
    ax.grid(True)

    return ax


def plot_calibration(y_true: np.ndarray, y_prob: np.ndarray, ax: Optional[plt.Axes] = None) -> plt.Axes:
    """
    Plot the calibration curve (reliability diagram).

    Args:
        y_true: True binary labels.
        y_prob: Predicted probabilities for the positive class.
        ax: Matplotlib axes to plot on. If None, creates a new figure.

    Returns:
        The matplotlib axes object.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    # Use 10 bins for calibration curve
    fraction_of_positives, mean_predicted_value = calibration_curve(y_true, y_prob, n_bins=10)

    ax.plot(mean_predicted_value, fraction_of_positives, "s-", label="Model", color="darkorange")
    ax.plot([0, 1], [0, 1], "k:", label="Perfectly calibrated")
    ax.set_xlabel("Mean Predicted Probability")
    ax.set_ylabel("Fraction of Positives")
    ax.set_title("Calibration Plot (Reliability Diagram)")
    ax.legend(loc="upper left")
    ax.grid(True)
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])

    return ax


def evaluate_model(
    y_true: np.ndarray, y_prob: np.ndarray, output_dir: Path
) -> Tuple[Dict[str, float], List[Path]]:
    """
    Perform full evaluation: compute metrics and generate plots.

    Args:
        y_true: True binary labels.
        y_prob: Predicted probabilities for the positive class.
        output_dir: Directory to save plots and metrics.

    Returns:
        Tuple of (metrics dictionary, list of saved file paths).

    Raises:
        AssertionError: If ROC-AUC is below the baseline (0.50).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []

    # Compute metrics
    metrics = compute_metrics(y_true, y_prob)

    # Assert baseline
    if metrics["roc_auc"] < BASELINE_ROC_AUC:
        raise AssertionError(
            f"ROC-AUC ({metrics['roc_auc']:.4f}) is below baseline ({BASELINE_ROC_AUC}). "
            "Model performance is worse than random guessing."
        )

    logger.info(f"Baseline assertion passed: ROC-AUC ({metrics['roc_auc']:.4f}) >= {BASELINE_ROC_AUC}")

    # Create figure for all plots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Plot ROC curve
    plot_roc_curve(y_true, y_prob, ax=axes[0, 0])
    roc_path = output_dir / "roc_curve.png"
    fig.axes[0].figure.savefig(roc_path, dpi=FIGURE_DPI, bbox_inches="tight")
    saved_files.append(roc_path)

    # Plot PR curve
    plot_pr_curve(y_true, y_prob, ax=axes[0, 1])
    pr_path = output_dir / "pr_curve.png"
    fig.axes[1].figure.savefig(pr_path, dpi=FIGURE_DPI, bbox_inches="tight")
    saved_files.append(pr_path)

    # Plot Calibration curve
    plot_calibration(y_true, y_prob, ax=axes[1, 0])
    cal_path = output_dir / "calibration_curve.png"
    fig.axes[2].figure.savefig(cal_path, dpi=FIGURE_DPI, bbox_inches="tight")
    saved_files.append(cal_path)

    # Add a summary text in the last subplot
    axes[1, 1].axis("off")
    metrics_text = (
        f"Evaluation Metrics:\n"
        f"ROC-AUC: {metrics['roc_auc']:.4f}\n"
        f"PR-AUC: {metrics['pr_auc']:.4f}\n\n"
        f"Baseline Check: {'PASSED' if metrics['roc_auc'] >= BASELINE_ROC_AUC else 'FAILED'}"
    )
    axes[1, 1].text(
        0.1, 0.5, metrics_text, fontsize=12, family="monospace",
        transform=axes[1, 1].transAxes, verticalalignment="center"
    )
    summary_path = output_dir / "evaluation_summary.png"
    fig.savefig(summary_path, dpi=FIGURE_DPI, bbox_inches="tight")
    saved_files.append(summary_path)

    plt.close(fig)

    # Save metrics as JSON
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    saved_files.append(metrics_path)

    logger.info(f"Saved evaluation artifacts to {output_dir}")
    return metrics, saved_files


def save_metrics(metrics: Dict[str, float], output_path: Path) -> None:
    """
    Save metrics to a JSON file.

    Args:
        metrics: Dictionary of metrics.
        output_path: Path to save the JSON file.
    """
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {output_path}")


def main() -> None:
    """
    Main entry point for the evaluation script.

    Parses arguments, loads data and model, evaluates the model,
    and saves results.
    """
    parser = argparse.ArgumentParser(description="Evaluate model performance on test data.")
    parser.add_argument(
        "--data-dir", type=Path, required=True, help="Directory containing train/test splits and models."
    )
    parser.add_argument(
        "--model-path", type=Path, required=True, help="Path to the trained model pickle file."
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/model"), help="Directory to save evaluation outputs."
    )
    parser.add_argument(
        "--test-data", type=Path, default=Path("data/test_data.csv"), help="Path to the test data CSV."
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Resolve paths
    data_dir = args.data_dir
    model_path = args.model_path
    output_dir = args.output_dir
    test_data_path = args.test_data

    if not test_data_path.is_absolute():
        test_data_path = data_dir.parent / test_data

    if not model_path.is_absolute():
        model_path = data_dir / model_path

    try:
        # Load data
        logger.info(f"Loading test data from {test_data_path}")
        df, X_test, y_test = load_test_data(test_data_path)

        # Load model
        logger.info(f"Loading model from {model_path}")
        model = load_model(model_path)

        # Predict probabilities
        logger.info("Generating predictions...")
        if hasattr(model, "predict_proba"):
            y_prob = model.predict_proba(X_test)[:, 1]
        else:
            # Fallback for models without predict_proba (e.g., some simple estimators)
            logger.warning("Model does not have predict_proba. Using decision_function or predict.")
            if hasattr(model, "decision_function"):
                y_scores = model.decision_function(X_test)
                # Normalize to [0, 1] if possible, otherwise use raw scores
                # For ROC-AUC, raw scores are acceptable if monotonic
                y_prob = y_scores
            else:
                y_pred = model.predict(X_test)
                y_prob = y_pred.astype(float)

        # Evaluate
        logger.info("Evaluating model...")
        metrics, saved_files = evaluate_model(y_test, y_prob, output_dir)

        # Print summary
        print("\n" + "="*50)
        print("EVALUATION SUMMARY")
        print("="*50)
        for key, value in metrics.items():
            print(f"{key}: {value:.4f}")
        print("="*50)
        print(f"Saved artifacts: {[str(f) for f in saved_files]}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except AssertionError as e:
        logger.error(f"Baseline assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()