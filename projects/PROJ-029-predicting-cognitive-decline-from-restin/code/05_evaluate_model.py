"""Evaluate the trained model and write a performance report.

This script loads the feature matrix and labels, loads the trained model
(produced by ``code/04_train_model.py``), performs a 5‑fold stratified
cross‑validation, computes ROC‑AUC, accuracy and F1‑score for each fold,
aggregates the results and writes them to
``data/processed/performance_report.json``.
"""

import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

# Local utilities
from utils.io import ensure_dir, load_csv, save_json
from utils.logger import get_logger


# ----------------------------------------------------------------------
# Helper / wrapper functions
# ----------------------------------------------------------------------

def get_logger_wrapper(name: str = "evaluate_model"):
    """Return a tolerant logger instance."""
    return get_logger(name)


def load_features_and_labels(
    features_path: Path = Path("data/processed/graph_metrics.csv")
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Load the feature matrix and the binary decline label.

    The decline label is defined as a drop of ≥3 points on either the MMSE
    or MOCA between the two longitudinal assessments.  The original
    training script (``04_train_model.py``) creates the same label, so we
    replicate the logic here for consistency.
    """
    logger = get_logger_wrapper()
    logger.info("Loading features from %s", features_path)

    if not features_path.is_file():
        logger.error("Feature file not found: %s", features_path)
        raise FileNotFoundError(features_path)

    df = load_csv(features_path)
    # Expect a column named 'subject_id' and columns for the graph metrics.
    # The label columns are 'mmse_t1', 'mmse_t2', 'moca_t1', 'moca_t2'.
    required_label_cols = {"mmse_t1", "mmse_t2", "moca_t1", "moca_t2"}
    missing = required_label_cols - set(df.columns)
    if missing:
        logger.error("Missing required label columns: %s", missing)
        raise KeyError(f"Missing label columns: {missing}")

    # Compute decline label
    mmse_drop = df["mmse_t1"] - df["mmse_t2"]
    moca_drop = df["moca_t1"] - df["moca_t2"]
    decline = ((mmse_drop >= 3) | (moca_drop >= 3)).astype(int)

    # Features are all columns except the raw scores and subject_id
    feature_cols = [c for c in df.columns if c not in required_label_cols | {"subject_id"}]
    X = df[feature_cols].copy()
    y = decline
    logger.info("Loaded %d subjects with %d features", X.shape[0], X.shape[1])
    return X, y


def load_trained_model(
    model_path: Path = Path("data/processed/model.pkl")
) -> object:
    """Load the pickled scikit‑learn model."""
    logger = get_logger_wrapper()
    logger.info("Loading trained model from %s", model_path)
    if not model_path.is_file():
        logger.error("Model file not found: %s", model_path)
        raise FileNotFoundError(model_path)
    model = joblib.load(model_path)
    logger.info("Model loaded successfully")
    return model


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None = None,
) -> dict:
    """Return ROC‑AUC, accuracy and F1‑score for a single fold."""
    # ROC‑AUC requires probability estimates for the positive class.
    if y_proba is None:
        # Fall back to using the binary predictions (will give 0.5 if
        # predictions are perfectly balanced).  This is a safe default.
        roc_auc = float("nan")
    else:
        roc_auc = roc_auc_score(y_true, y_proba[:, 1])
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    return {"roc_auc": roc_auc, "accuracy": acc, "f1": f1}


def evaluate_model(
    n_splits: int = 5,
    random_state: int = 42,
    output_path: Path = Path("data/processed/performance_report.json"),
) -> None:
    """Run stratified CV, compute metrics per fold, and write a JSON report."""
    logger = get_logger_wrapper()
    logger.info("Starting model evaluation with %d‑fold CV", n_splits)

    X, y = load_features_and_labels()
    model = load_trained_model()

    cv = StratifiedKFold(
        n_splits=n_splits, shuffle=True, random_state=random_state
    )

    fold_results = []
    for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y), start=1):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        # Fit a fresh copy of the model for each outer fold
        fitted = joblib.clone(model)
        fitted.fit(X_train, y_train)

        # Predict probabilities if supported
        if hasattr(fitted, "predict_proba"):
            y_proba = fitted.predict_proba(X_test)
        else:
            y_proba = None

        y_pred = fitted.predict(X_test)
        metrics = calculate_metrics(y_test.values, y_pred, y_proba)
        metrics["fold"] = fold_idx
        fold_results.append(metrics)
        logger.info(
            "Fold %d – ROC‑AUC: %.3f, Acc: %.3f, F1: %.3f",
            fold_idx,
            metrics["roc_auc"],
            metrics["accuracy"],
            metrics["f1"],
        )

    # Compute means (ignore NaN ROC‑AUC if any)
    means = {
        "roc_auc": float(np.nanmean([r["roc_auc"] for r in fold_results])),
        "accuracy": float(np.mean([r["accuracy"] for r in fold_results])),
        "f1": float(np.mean([r["f1"] for r in fold_results])),
    }

    report = {"folds": fold_results, "mean": means}

    # Ensure the output directory exists
    ensure_dir(output_path.parent)
    save_json(report, output_path)
    logger.info("Performance report written to %s", output_path)


def main() -> None:
    """Entry point for the script."""
    evaluate_model()


if __name__ == "__main__":
    sys.exit(main())
