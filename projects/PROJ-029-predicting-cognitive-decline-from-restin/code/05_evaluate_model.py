"""Evaluate the trained Random Forest model.

This script loads the eligible subjects list, the feature matrix (including the
binary decline label), the persisted model, computes ROC‑AUC, accuracy and
F1‑score, and writes a JSON performance report to
``data/processed/performance_report.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

# Local imports – the utils package provides robust I/O helpers
from utils.io import load_csv, load_pickle, save_json
from utils.logger import get_logger

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def get_logger_wrapper(name: str | None = None):
    """Return a reproducibility‑compatible logger.

    The project defines a tolerant logger in ``utils.logger``; this wrapper
    mirrors the historic signature used throughout the code base.
    """
    if name:
        return get_logger(name)
    return get_logger()

def ensure_file(path: Path) -> None:
    """Exit with a clear message if *path* does not exist."""
    if not path.is_file():
        logger = get_logger_wrapper()
        logger.error(f"Required file not found: {path}")
        sys.exit(1)

def load_eligible_subjects() -> Path:
    """Return the path to the CSV containing eligible subject IDs."""
    csv_path = Path("data/processed/eligible_subjects.csv")
    ensure_file(csv_path)
    return csv_path

def load_features() -> Path:
    """Return the path to the CSV containing the feature matrix."""
    csv_path = Path("data/processed/graph_metrics.csv")
    ensure_file(csv_path)
    return csv_path

def split_features_labels(df):
    """Split a DataFrame into features (X) and binary label (y).

    The label column is expected to be named ``decline`` – this matches the
    output of ``code/04_train_model.py``. If the column is missing, the
    function raises a helpful error.
    """
    label_col = "decline"
    if label_col not in df.columns:
        logger = get_logger_wrapper()
        logger.error(
            f"Label column '{label_col}' not found in features CSV. "
            f"Available columns: {list(df.columns)}"
        )
        sys.exit(1)
    y = df[label_col].astype(int).values
    X = df.drop(columns=[label_col]).values
    return X, y

def load_trained_model() -> Path:
    """Return the path to the persisted Random Forest model."""
    model_path = Path("data/processed/model.pkl")
    ensure_file(model_path)
    return model_path

def isnan(x: Any) -> bool:
    """Return ``True`` if *x* is NaN (covers Python float and NumPy)."""
    try:
        return np.isnan(x)
    except Exception:
        return False

def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None = None,
) -> Dict[str, float]:
    """Compute ROC‑AUC, accuracy and F1‑score.

    ``y_proba`` should contain the probability of the positive class.
    If it is ``None`` or contains NaNs, ROC‑AUC is reported as ``nan``.
    """
    metrics: Dict[str, float] = {}

    # Accuracy and F1 are always computable
    metrics["accuracy"] = float(accuracy_score(y_true, y_pred))
    metrics["f1_score"] = float(f1_score(y_true, y_pred, zero_division=0))

    # ROC‑AUC – guard against missing or invalid probabilities
    if y_proba is None or np.isnan(y_proba).any():
        metrics["roc_auc"] = float("nan")
    else:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba))
        except Exception:
            metrics["roc_auc"] = float("nan")
    return metrics

def write_performance_report(report: Dict[str, Any]) -> None:
    """Write the performance dictionary to JSON."""
    output_path = Path("data/processed/performance_report.json")
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(report, output_path)
    logger = get_logger_wrapper()
    logger.info(f"Performance report written to {output_path}")

# ----------------------------------------------------------------------
# Main evaluation routine
# ----------------------------------------------------------------------
def evaluate_model() -> None:
    """Load data, evaluate the persisted model, and write a JSON report."""
    logger = get_logger_wrapper("evaluate_model")
    logger.info("Starting model evaluation")

    # Load inputs
    eligible_path = load_eligible_subjects()
    features_path = load_features()
    model_path = load_trained_model()

    # Read CSVs
    eligible_df = load_csv(eligible_path)
    features_df = load_csv(features_path)

    # Align features with eligible subjects (defensive programming)
    if "subject_id" in eligible_df.columns and "subject_id" in features_df.columns:
        merged = pd.merge(
            eligible_df, features_df, on="subject_id", how="inner"
        )
        if merged.empty:
            logger.error("No overlapping subject IDs between eligible list and features.")
            sys.exit(1)
        X, y = split_features_labels(merged)
    else:
        # Fall back to using the full features dataframe
        X, y = split_features_labels(features_df)

    # Load the model
    model = load_pickle(model_path)

    # Predict
    try:
        y_pred = model.predict(X)
    except Exception as e:
        logger.error(f"Model prediction failed: {e}")
        sys.exit(1)

    # Probability for ROC‑AUC (binary classification)
    y_proba = None
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(X)
            # Positive class is assumed to be the second column
            y_proba = proba[:, 1] if proba.shape[1] == 2 else proba[:, 0]
        except Exception:
            logger.warning("Could not obtain prediction probabilities; ROC‑AUC will be NaN.")

    # Compute metrics
    metrics = calculate_metrics(y, y_pred, y_proba)

    # Assemble report
    report = {
        "roc_auc": metrics["roc_auc"],
        "accuracy": metrics["accuracy"],
        "f1_score": metrics["f1_score"],
        "n_samples": int(len(y)),
    }

    # Write JSON report
    write_performance_report(report)
    logger.info("Model evaluation completed successfully")

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """CLI entry point."""
    evaluate_model()

if __name__ == "__main__":
    main()
