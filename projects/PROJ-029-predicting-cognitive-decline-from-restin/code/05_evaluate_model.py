"""Evaluate a trained Random Forest model using cross‑validation.

This script loads the processed graph metrics (features) and the eligible
subject list (including the decline label), performs a 5‑fold stratified
cross‑validation, computes ROC‑AUC, accuracy and F1‑score for each fold,
aggregates the results and writes them to ``data/processed/performance_report.json``.

The implementation is deliberately self‑contained: it does **not** depend
on the model produced by ``code/04_train_model.py`` (which may be missing
in earlier pipeline runs). Instead, it trains a fresh ``RandomForestClassifier``
inside each CV fold using the same hyper‑parameters that the training script
would have used (``n_estimators=100`` and ``max_depth=None``).  This guarantees
that the evaluation step can run independently and still produce a realistic
performance report.

The script can be executed directly::

    python code/05_evaluate_model.py

It will create ``data/processed/performance_report.json`` on success.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def get_logger_wrapper(name: str | None = None) -> Any:
    """
    Return a logger compatible with the project's reproducibility logger.

    The project's ``utils.logger`` module provides a tolerant ``get_logger``
    implementation.  Importing it lazily avoids circular imports.
    """
    from utils.logger import get_logger

    return get_logger(name) if name else get_logger()

def ensure_file(path: Path) -> None:
    """Raise a clear error if ``path`` does not exist."""
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")

def isnan(value: Any) -> bool:
    """Return ``True`` for NaN or ``None`` values."""
    return value is None or (isinstance(value, float) and np.isnan(value))

# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def load_eligible_subjects() -> Path:
    """
    Return the path to the CSV file that lists eligible subjects and their
    decline label.  The file is produced by ``code/01_download_and_filter.py``.
    """
    csv_path = Path("data/processed/eligible_subjects.csv")
    ensure_file(csv_path)
    return csv_path

def load_features() -> Path:
    """
    Return the path to the CSV file containing graph‑metric features.
    Produced by ``code/03_compute_graph_metrics.py``.
    """
    csv_path = Path("data/processed/graph_metrics.csv")
    ensure_file(csv_path)
    return csv_path

# --------------------------------------------------------------------------- #
# Core processing
# --------------------------------------------------------------------------- #
def split_features_labels(
    features_path: Path, subjects_path: Path
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load ``features_path`` and ``subjects_path`` and return ``X`` (feature matrix)
    and ``y`` (binary decline label).

    Both CSV files are expected to contain a ``subject_id`` column that can be
    used to align rows.
    """
    import pandas as pd

    # Load CSVs
    df_features = pd.read_csv(features_path)
    df_subjects = pd.read_csv(subjects_path)

    # Ensure the key column exists
    if "subject_id" not in df_features.columns or "subject_id" not in df_subjects.columns:
        raise KeyError(
            "Both feature and subject CSVs must contain a 'subject_id' column."
        )

    # Merge on subject_id to keep only eligible subjects
    df = pd.merge(df_subjects, df_features, on="subject_id", how="inner")

    if "decline_label" not in df.columns:
        raise KeyError(
            "The eligible subjects file must contain a 'decline_label' column."
        )

    # Separate target and features; drop non‑numeric columns
    y = df["decline_label"].values
    X = df.drop(columns=["subject_id", "decline_label"]).select_dtypes(include=[np.number])

    # Replace NaNs with column means (a simple imputation strategy)
    X = X.fillna(X.mean()).to_numpy()
    return X, y

def calculate_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray
) -> Dict[str, float]:
    """
    Compute ROC‑AUC, accuracy and F1‑score.

    ``y_proba`` is expected to be the probability of the positive class.
    """
    # Guard against cases where only one class is present in y_true
    if len(np.unique(y_true)) == 1:
        roc_auc = float("nan")
    else:
        roc_auc = roc_auc_score(y_true, y_proba)

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    return {"roc_auc": roc_auc, "accuracy": acc, "f1": f1}

def evaluate_model(
    X: np.ndarray, y: np.ndarray, n_splits: int = 5, random_state: int = 42
) -> Tuple[List[Dict[str, float]], Dict[str, float]]:
    """
    Perform stratified K‑fold cross‑validation, train a Random Forest on each
    training split and compute metrics on the held‑out split.

    Returns a list of per‑fold metric dictionaries and a dictionary of mean
    values across folds.
    """
    logger = get_logger_wrapper("evaluate_model")
    logger.info("Starting cross‑validation evaluation")

    skf = StratifiedKFold(
        n_splits=n_splits, shuffle=True, random_state=random_state
    )
    fold_metrics: List[Dict[str, float]] = []

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y), start=1):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Model hyper‑parameters match the FR‑003 requirement
        clf = RandomForestClassifier(
            n_estimators=100, max_depth=None, random_state=random_state, n_jobs=1
        )
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        y_proba = clf.predict_proba(X_test)[:, 1]

        metrics = calculate_metrics(y_test, y_pred, y_proba)
        metrics["fold"] = fold_idx
        fold_metrics.append(metrics)

        logger.info(
            f"Fold {fold_idx}: ROC‑AUC={metrics['roc_auc']:.3f}, "
            f"Acc={metrics['accuracy']:.3f}, F1={metrics['f1']:.3f}"
        )

    # Compute means, ignoring NaNs (e.g., ROC‑AUC when a fold has a single class)
    means: Dict[str, float] = {
        "roc_auc": np.nanmean([m["roc_auc"] for m in fold_metrics]),
        "accuracy": np.mean([m["accuracy"] for m in fold_metrics]),
        "f1": np.mean([m["f1"] for m in fold_metrics]),
    }

    logger.info(
        f"Cross‑validation completed. Mean ROC‑AUC={means['roc_auc']:.3f}, "
        f"Mean Acc={means['accuracy']:.3f}, Mean F1={means['f1']:.3f}"
    )
    return fold_metrics, means

def write_performance_report(
    fold_metrics: List[Dict[str, float]],
    mean_metrics: Dict[str, float],
    output_path: Path = Path("data/processed/performance_report.json"),
) -> None:
    """Serialize the evaluation results to JSON."""
    report = {"folds": fold_metrics, "mean": mean_metrics}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    logger = get_logger_wrapper("evaluate_model")
    try:
        subjects_path = load_eligible_subjects()
        features_path = load_features()
        X, y = split_features_labels(features_path, subjects_path)

        fold_metrics, mean_metrics = evaluate_model(X, y)
        write_performance_report(fold_metrics, mean_metrics)

        logger.info(
            f"Performance report written to "
            f"{Path('data/processed/performance_report.json')}"
        )
    except Exception as exc:
        logger.error(f"Evaluation failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
