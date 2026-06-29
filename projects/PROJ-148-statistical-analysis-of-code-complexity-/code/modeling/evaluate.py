"""
Evaluation script for the bug prediction models.

This script loads a trained model (by default the primary logistic regression
model saved at ``data/model/primary.pkl``) and a test dataset (by default
``data/processed/test.csv``).  It computes the following evaluation metrics:

* ROC‑AUC
* PR‑AUC (average precision)
* Calibration curve (saved as a PNG)

The results are written to ``data/model/evaluation_metrics.json`` and the
calibration plot to ``data/model/calibration_plot.png``.

An assertion is raised if the ROC‑AUC does not meet the baseline of 0.50.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import average_precision_score, roc_auc_score

DEFAULT_TEST_PATH = Path("data/processed/test.csv")
DEFAULT_MODEL_PATH = Path("data/model/primary.pkl")
DEFAULT_OUTPUT_DIR = Path("data/model")
METRICS_FILENAME = "evaluation_metrics.json"
CALIBRATION_PLOT_FILENAME = "calibration_plot.png"

def load_test_data(test_path: Path) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the test dataset and split it into features (X) and target (y).

    The test CSV is expected to contain a ``bug_label`` column that holds
    the binary target. All remaining columns are treated as features.

    Parameters
    ----------
    test_path: Path
        Path to the CSV file containing the test split.

    Returns
    -------
    X: pd.DataFrame
        Feature matrix.
    y: pd.Series
        Binary target vector.
    """
    if not test_path.is_file():
        raise FileNotFoundError(f"Test data not found at {test_path}")

    df = pd.read_csv(test_path)
    if "bug_label" not in df.columns:
        raise ValueError("Test data must contain a 'bug_label' column.")

    y = df["bug_label"]
    X = df.drop(columns=["bug_label"])
    return X, y

def load_model(model_path: Path):
    """
    Load a scikit‑learn model saved with joblib.

    Parameters
    ----------
    model_path: Path
        Path to the serialized model file.

    Returns
    -------
    model: Any
        The deserialized model object.
    """
    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found at {model_path}")

    return joblib.load(model_path)

def compute_metrics(y_true: np.ndarray, y_proba: np.ndarray) -> dict:
    """
    Compute ROC‑AUC and PR‑AUC (average precision).

    Parameters
    ----------
    y_true: np.ndarray
        Ground‑truth binary labels.
    y_proba: np.ndarray
        Predicted probability for the positive class.

    Returns
    -------
    dict
        Mapping with ``roc_auc`` and ``pr_auc`` keys.
    """
    roc_auc = roc_auc_score(y_true, y_proba)
    pr_auc = average_precision_score(y_true, y_proba)
    return {"roc_auc": float(roc_auc), "pr_auc": float(pr_auc)}

def plot_calibration(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    output_path: Path,
    n_bins: int = 10,
) -> None:
    """
    Generate a calibration curve plot and save it as a PNG.

    Parameters
    ----------
    y_true: np.ndarray
        Ground‑truth binary labels.
    y_proba: np.ndarray
        Predicted probability for the positive class.
    output_path: Path
        Destination file for the PNG plot.
    n_bins: int, optional
        Number of bins to use for the calibration curve.
    """
    prob_true, prob_pred = calibration_curve(y_true, y_proba, n_bins=n_bins)

    plt.figure(figsize=(6, 6))
    plt.plot(prob_pred, prob_true, marker="o", linewidth=1, label="Model")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfectly calibrated")
    plt.title("Calibration Curve")
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Fraction of positives")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()

def evaluate_model(
    test_path: Path = DEFAULT_TEST_PATH,
    model_path: Path = DEFAULT_MODEL_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict:
    """
    Full evaluation pipeline.

    Loads data and model, computes metrics, creates a calibration plot,
    writes the metrics to a JSON file, and asserts the ROC‑AUC baseline.

    Parameters
    ----------
    test_path: Path
        Path to the test CSV.
    model_path: Path
        Path to the serialized model.
    output_dir: Path
        Directory where evaluation artifacts are stored.

    Returns
    -------
    dict
        Dictionary containing the computed metrics.
    """
    X_test, y_test = load_test_data(test_path)
    model = load_model(model_path)

    if not hasattr(model, "predict_proba"):
        raise AttributeError("Model does not implement `predict_proba` required for evaluation.")

    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = compute_metrics(y_test.values, y_proba)

    # Assert baseline ROC‑AUC
    if metrics["roc_auc"] < 0.50:
        raise AssertionError(f"ROC‑AUC {metrics['roc_auc']:.3f} is below the required baseline of 0.50.")

    # Write metrics JSON
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / METRICS_FILENAME
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Create calibration plot
    calibration_path = output_dir / CALIBRATION_PLOT_FILENAME
    plot_calibration(y_test.values, y_proba, calibration_path)

    return metrics

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate bug‑prediction model.")
    parser.add_argument(
        "--test-path",
        type=Path,
        default=DEFAULT_TEST_PATH,
        help=f"Path to test CSV (default: {DEFAULT_TEST_PATH})",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help=f"Path to serialized model (default: {DEFAULT_MODEL_PATH})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to write evaluation artifacts (default: {DEFAULT_OUTPUT_DIR})",
    )
    return parser

def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    try:
        metrics = evaluate_model(
            test_path=args.test_path,
            model_path=args.model_path,
            output_dir=args.output_dir,
        )
        print(f"Evaluation completed successfully. Metrics written to {args.output_dir / METRICS_FILENAME}")
        print(json.dumps(metrics, indent=2))
    except Exception as exc:
        # Re‑raise after printing a friendly message – the test suite expects a non‑zero exit
        print(f"Evaluation failed: {exc}")
        raise

if __name__ == "__main__":
    main()
