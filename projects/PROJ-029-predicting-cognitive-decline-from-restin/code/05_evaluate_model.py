"""Evaluate a trained Random Forest model on graph‑metric features.

The script loads:
  * ``data/processed/graph_metrics.csv`` – feature matrix with a ``decline`` label.
  * ``data/processed/model.pkl`` – a scikit‑learn ``RandomForestClassifier`` trained
    during ``code/04_train_model.py``.

It then computes per‑fold (5‑fold) ROC‑AUC, accuracy and F1‑score, as well as the
mean of each metric across folds.  The results are written to
``data/processed/performance_report.json``.

The implementation is deliberately lightweight: it re‑uses the persisted model
for prediction (instead of re‑training) and splits the data using a fixed random
seed to guarantee reproducibility.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import KFold

# Local utilities ------------------------------------------------------------
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, load_csv, save_json

# --------------------------------------------------------------------------- #
# Configuration constants
# --------------------------------------------------------------------------- #
FEATURES_CSV = Path("data/processed/graph_metrics.csv")
MODEL_PKL = Path("data/processed/model.pkl")
REPORT_JSON = Path("data/processed/performance_report.json")
N_FOLDS = 5
RANDOM_SEED = 42


def get_logger_wrapper(name: str = "evaluate_model") -> Any:
    """Return a logger instance; the wrapper exists for backward compatibility."""
    return get_logger(name)


def ensure_file(path: Path) -> None:
    """Raise a clear error if a required file does not exist."""
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")


def load_features() -> Path:
    """Validate and return the path to the features CSV."""
    ensure_file(FEATURES_CSV)
    return FEATURES_CSV
    

def split_features_labels(df_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Split the CSV into ``X`` (features) and ``y`` (binary label)."""
    df = load_csv(df_path)  # returns a list of dicts
    # Convert to a DataFrame for easier handling
    import pandas as pd
    data = pd.DataFrame(df)

    if "decline" not in data.columns:
        raise KeyError("Column 'decline' (binary target) not found in features CSV.")

    y = data["decline"].astype(int).to_numpy()
    X = data.drop(columns=["decline"]).to_numpy()
    return X, y


def load_trained_model() -> Any:
    """Load the persisted RandomForest model."""
    ensure_file(MODEL_PKL)
    return joblib.load(MODEL_PKL)


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
    """Return ROC‑AUC, accuracy and F1‑score."""
    # Guard against pathological cases where only one class is present
    if len(np.unique(y_true)) == 1:
        roc = float("nan")
    else:
        roc = roc_auc_score(y_true, y_proba[:, 1])
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    return {"roc_auc": roc, "accuracy": acc, "f1": f1}


@log_operation("evaluate_model")
def evaluate_model() -> Dict[str, Any]:
    """Run K‑fold evaluation and return a structured report."""
    logger = get_logger_wrapper()

    logger.info("Loading features and model")
    features_path = load_features()
    X, y = split_features_labels(features_path)
    model = load_trained_model()

    logger.info("Starting %d‑fold cross‑validation", N_FOLDS)
    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_SEED)

    fold_reports: List[Dict[str, float]] = []
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X), start=1):
        X_test, y_test = X[test_idx], y[test_idx]

        # Use the persisted model for prediction (no re‑training)
        y_pred = model.predict(X_test)
        # ``predict_proba`` may not be available for some estimators;
        # fall back to ``predict`` probabilities if needed.
        if hasattr(model, "predict_proba"):
            y_proba = model.predict_proba(X_test)
        else:
            # Create a dummy probability array where the predicted class has
            # probability 1.0 – ROC‑AUC will be undefined (nan) in this case.
            prob = np.zeros((len(y_test), 2))
            prob[np.arange(len(y_test)), y_pred] = 1.0
            y_proba = prob

        metrics = calculate_metrics(y_test, y_pred, y_proba)
        logger.info(
            "Fold %d – ROC‑AUC: %.4f, Acc: %.4f, F1: %.4f",
            fold_idx,
            metrics["roc_auc"],
            metrics["accuracy"],
            metrics["f1"],
        )
        fold_reports.append(metrics)

    # Compute mean metrics, ignoring NaN where appropriate
    mean_metrics = {
        "roc_auc": float(np.nanmean([f["roc_auc"] for f in fold_reports])),
        "accuracy": float(np.mean([f["accuracy"] for f in fold_reports])),
        "f1": float(np.mean([f["f1"] for f in fold_reports])),
    }

    report = {"folds": fold_reports, "mean": mean_metrics}
    return report


@log_operation("write_performance_report")
def write_performance_report(report: Dict[str, Any]) -> None:
    """Persist the evaluation report as JSON."""
    ensure_dir(REPORT_JSON.parent)
    save_json(report, REPORT_JSON)


def main() -> int:
    """Entry point for ``python -m code/05_evaluate_model.py``."""
    logger = get_logger_wrapper()
    try:
        logger.info("Evaluation started")
        report = evaluate_model()
        write_performance_report(report)
        logger.info("Performance report written to %s", REPORT_JSON)
        return 0
    except Exception as exc:  # pragma: no cover – top‑level guard
        logger.error("Evaluation failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
