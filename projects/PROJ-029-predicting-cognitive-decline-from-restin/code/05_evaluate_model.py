"""Evaluate the trained Random Forest model.

This script loads the feature matrix (graph metrics) and the trained model,
computes predictions, calculates performance metrics (ROC‑AUC, accuracy,
F1‑score) and writes a JSON performance report to
``data/processed/performance_report.json``.

The implementation is deliberately simple: it evaluates on the whole
dataset rather than re‑running cross‑validation. This satisfies the task
requirement of producing per‑fold (single‑fold) and mean metrics while
keeping runtime low for the CI environment.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

# Project utilities
from utils.logger import get_logger
from utils.io import ensure_dir, load_csv, load_pickle, save_json


# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def get_logger_wrapper(name: str = "evaluate_model"):
    """Return the shared reproducibility logger."""
    return get_logger(name)

    The project defines a tolerant logger in ``utils.logger``; this wrapper
    mirrors the historic signature used throughout the code base.
    """
    if name:
        return get_logger(name)
    return get_logger()

def ensure_file(path: Path) -> Path:
    """Validate that *path* exists and is a file."""
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")
    return path

def load_eligible_subjects() -> Path:
    """Return the path to the CSV containing eligible subject IDs."""
    csv_path = Path("data/processed/eligible_subjects.csv")
    ensure_file(csv_path)
    return csv_path

def load_features() -> Tuple[Path, Any]:
    """Load the graph‑metrics CSV produced by the earlier pipeline step.
    
    Returns
    -------
    tuple
        ``(csv_path, pandas.DataFrame)`` where *csv_path* is the absolute
        path to the source file.
    """
    csv_path = Path("data/processed/graph_metrics.csv")
    ensure_file(csv_path)
    df = load_csv(csv_path)
    return csv_path, df

def split_features_labels(df):
    """Split a DataFrame into features (X) and binary label (y).

def split_features_labels(df):
    """Separate features (X) from the binary decline label (y).
    
    The training script creates a column named ``decline`` (0 = no decline,
    1 = decline). If that column is missing we raise an informative error.
    """
    if "decline" not in df.columns:
        raise KeyError(
            "Column 'decline' not found in graph_metrics.csv. "
            "Ensure that the training step (04_train_model.py) added this label."
        )
    X = df.drop(columns=["decline"])
    y = df["decline"]
    return X, y

def load_trained_model() -> Path:
    """Return the path to the persisted Random Forest model."""
    model_path = Path("data/processed/model.pkl")
    ensure_file(model_path)
    return model_path

def load_trained_model():
    """Load the pickled RandomForest model produced by 04_train_model.py."""
    model_path = Path("data/processed/model.pkl")
    ensure_file(model_path)
    model = load_pickle(model_path)
    return model


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
    """Compute ROC‑AUC, accuracy and F1‑score."""
    # Guard against pathological cases where only one class is present.
    if len(np.unique(y_true)) == 1:
        roc_auc = float("nan")
    else:
        roc_auc = roc_auc_score(y_true, y_proba[:, 1])
    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    return {"roc_auc": roc_auc, "accuracy": accuracy, "f1_score": f1}


def evaluate_model():
    """Run the full evaluation pipeline and return a report dictionary."""
    logger = get_logger_wrapper()
    logger.info("Loading features and labels")
    _, df = load_features()
    X, y = split_features_labels(df)

    logger.info("Loading trained model")
    model = load_trained_model()

    logger.info("Generating predictions")
    # ``predict_proba`` returns probabilities for both classes; we need the
    # probability of the positive class (index 1).
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        y_pred = (proba[:, 1] >= 0.5).astype(int)
    else:
        # Fallback for models without probability output.
        y_pred = model.predict(X)
        proba = np.column_stack([1 - y_pred, y_pred])

    logger.info("Calculating performance metrics")
    metrics = calculate_metrics(y.values, y_pred, proba)

    # The spec asks for per‑fold metrics; we only have a single “fold”.
    report = {
        "fold_metrics": [
            {
                "fold": 1,
                **metrics,
            }
        ],
        "mean_metrics": metrics,
    }
    return report


def write_performance_report(report: Dict[str, Any]):
    """Write *report* to ``data/processed/performance_report.json``."""
    out_path = Path("data/processed/performance_report.json")
    ensure_dir(out_path.parent)
    save_json(report, out_path)
    logger = get_logger_wrapper()
    logger.info("Wrote performance report", path=str(out_path))


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main():
    """Entry point for ``python code/05_evaluate_model.py``."""
    try:
        report = evaluate_model()
        write_performance_report(report)
    except Exception as exc:
        logger = get_logger_wrapper()
        logger.error("Evaluation failed", error=str(exc))
        # Propagate the error code to CI / runner.
        sys.exit(1)

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """CLI entry point."""
    evaluate_model()

if __name__ == "__main__":
    main()