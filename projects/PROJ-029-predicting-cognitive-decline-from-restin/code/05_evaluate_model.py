"""Evaluate the trained Random Forest model.

This script loads the feature matrix and binary decline labels, loads the
trained model (saved by ``code/04_train_model.py``), performs a 5‑fold
stratified cross‑validation, computes ROC‑AUC, accuracy and F1‑score for
each fold and the mean across folds, and writes the results to
``data/processed/performance_report.json``.

The public API mirrors the original specification:
  - ``get_logger_wrapper``
  - ``load_features_and_labels``
  - ``load_trained_model``
  - ``calculate_metrics``
  - ``evaluate_model``
  - ``write_performance_report``
  - ``main``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
from sklearn.base import clone
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

# Project utilities
from utils.io import load_csv, ensure_dir
from utils.logger import get_logger

# ----------------------------------------------------------------------
# Helper / public functions
# ----------------------------------------------------------------------

def get_logger_wrapper(name: str = "evaluate_model"):
    """Return a reproducibility‑aware logger."""
    # ``utils.logger.get_logger`` returns a singleton; the name argument is
    # accepted for compatibility with historic call‑sites.
    return get_logger(name)


def load_features_and_labels() -> Tuple[Path, List[str], List[int]]:
    """
    Load the feature matrix and binary labels.

    Returns
    -------
    X_path : pathlib.Path
        Path to the feature CSV (used for debugging / provenance).
    X : list of list
        Feature rows (list of numeric values).
    y : list of int
        Binary decline label (0 = stable, 1 = declined).
    """
    logger = get_logger_wrapper()

    # Expected locations (hard‑coded by the pipeline)
    graph_metrics_path = Path("data/processed/graph_metrics.csv")
    eligible_subjects_path = Path("data/processed/eligible_subjects.csv")

    if not graph_metrics_path.is_file():
        logger.error(f"Missing graph metrics file: {graph_metrics_path}")
        sys.exit(1)
    if not eligible_subjects_path.is_file():
        logger.error(f"Missing eligible subjects file: {eligible_subjects_path}")
        sys.exit(1)

    logger.info("Loading graph metrics")
    metrics_df = load_csv(graph_metrics_path)
    logger.info("Loading eligible subjects")
    subjects_df = load_csv(eligible_subjects_path)

    # ``load_csv`` returns a list of dicts (via utils.io).  Convert to DataFrames
    # for convenient manipulation.
    import pandas as pd

    metrics_df = pd.DataFrame(metrics_df)
    subjects_df = pd.DataFrame(subjects_df)

    # Assume a column named ``subject_id`` exists in both files.
    if "subject_id" not in metrics_df.columns or "subject_id" not in subjects_df.columns:
        logger.error("Both CSVs must contain a 'subject_id' column.")
        sys.exit(1)

    # Merge on subject_id to align features with labels.
    merged = pd.merge(metrics_df, subjects_df, on="subject_id", how="inner")

    # Identify the label column.  The training script creates a binary column
    # called ``decline``; fall back to any column with only 0/1 values.
    label_col = "decline" if "decline" in merged.columns else None
    if label_col is None:
        # Find a binary column (excluding subject_id)
        possible = [
            col for col in merged.columns
            if col != "subject_id" and merged[col].dropna().isin([0, 1]).all()
        ]
        if not possible:
            logger.error("Could not locate a binary decline label column.")
            sys.exit(1)
        label_col = possible[0]

    logger.info(f"Using label column '{label_col}'")

    # Features are all numeric columns except subject_id and the label.
    feature_cols = [
        col for col in merged.columns
        if col not in {"subject_id", label_col}
    ]

    X = merged[feature_cols].values.tolist()
    y = merged[label_col].astype(int).tolist()

    return X, feature_cols, y


def load_trained_model() -> Any:
    """Load the RandomForest model saved by the training step."""
    logger = get_logger_wrapper()
    model_path = Path("data/processed/model.pkl")
    if not model_path.is_file():
        logger.error(f"Trained model not found at {model_path}")
        sys.exit(1)
    logger.info(f"Loading trained model from {model_path}")
    return joblib.load(model_path)


def calculate_metrics(
    y_true: List[int],
    y_pred: List[int],
    y_proba: List[float] | None = None,
) -> Dict[str, float]:
    """Return ROC‑AUC, accuracy and F1‑score."""
    # Guard against degenerate cases where ROC‑AUC cannot be computed.
    if y_proba is None:
        roc = float("nan")
    else:
        try:
            roc = roc_auc_score(y_true, y_proba)
        except ValueError:
            roc = float("nan")
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    return {"roc_auc": roc, "accuracy": acc, "f1": f1}


def evaluate_model(
    X: List[List[float]],
    y: List[int],
    model: Any,
    n_splits: int = 5,
    random_state: int = 42,
) -> List[Dict[str, float]]:
    """
    Perform stratified K‑fold evaluation.

    Parameters
    ----------
    X, y : data
        Feature matrix and label vector.
    model : estimator
        A scikit‑learn estimator (will be cloned for each fold).
    n_splits : int
        Number of CV folds (default 5).
    random_state : int
        Seed for reproducibility.

    Returns
    -------
    List[dict]
        Per‑fold metric dictionaries.
    """
    logger = get_logger_wrapper()
    skf = StratifiedKFold(
        n_splits=n_splits, shuffle=True, random_state=random_state
    )
    per_fold: List[Dict[str, float]] = []

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y), start=1):
        logger.info(f"Evaluating fold {fold_idx}/{n_splits}")
        X_train = [X[i] for i in train_idx]
        y_train = [y[i] for i in train_idx]
        X_test = [X[i] for i in test_idx]
        y_test = [y[i] for i in test_idx]

        # Clone to avoid contaminating the original estimator.
        est = clone(model)
        est.fit(X_train, y_train)

        y_pred = est.predict(X_test)
        # ``predict_proba`` may not be available for some estimators; guard.
        if hasattr(est, "predict_proba"):
            y_proba = est.predict_proba(X_test)[:, 1].tolist()
        else:
            y_proba = None

        metrics = calculate_metrics(y_test, y_pred, y_proba)
        metrics["fold"] = fold_idx
        per_fold.append(metrics)

    return per_fold


def write_performance_report(
    per_fold: List[Dict[str, float]],
    output_path: Path = Path("data/processed/performance_report.json"),
) -> None:
    """Write per‑fold and mean metrics to JSON."""
    logger = get_logger_wrapper()
    ensure_dir(output_path.parent)

    # Compute means (ignore NaN for ROC‑AUC)
    import math

    mean_metrics = {
        "roc_auc": (
            sum(m["roc_auc"] for m in per_fold if not math.isnan(m["roc_auc"]))
            / max(
                1,
                sum(
                    1
                    for m in per_fold
                    if not math.isnan(m["roc_auc"])
                ),
            )
        ),
        "accuracy": sum(m["accuracy"] for m in per_fold) / len(per_fold),
        "f1": sum(m["f1"] for m in per_fold) / len(per_fold),
    }

    report = {"per_fold": per_fold, "mean": mean_metrics}

    logger.info(f"Writing performance report to {output_path}")
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)


def main() -> None:
    """Entry point for the evaluation script."""
    logger = get_logger_wrapper()
    logger.info("Starting model evaluation")

    X, feature_names, y = load_features_and_labels()
    logger.info(f"Loaded {len(X)} samples with {len(feature_names)} features")

    model = load_trained_model()

    per_fold_metrics = evaluate_model(X, y, model)
    write_performance_report(per_fold_metrics)

    logger.info("Model evaluation completed")


if __name__ == "__main__":
    main()