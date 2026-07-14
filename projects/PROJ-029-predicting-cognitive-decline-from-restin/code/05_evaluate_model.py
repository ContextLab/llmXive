"""Evaluate trained model performance.

This script loads the eligible subjects list, the computed graph metrics,
and the trained model. It performs a stratified K‑fold cross‑validation
(default 5 folds), training a fresh clone of the saved model on each
training split and evaluating on the held‑out test split. For every fold
the ROC‑AUC, accuracy and F1‑score are computed and the mean of each
metric across folds is written to ``data/processed/performance_report.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from joblib import load, dump, clone
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold


# --------------------------------------------------------------------------- #
# Helper utilities
# ----------------------------------------------------------------------
def get_logger_wrapper(name: str = "evaluate_model"):
    """Return a tolerant reproducibility logger.

    The project ships a custom logger implementation in ``utils.logger``.
    This wrapper simply forwards the request to that implementation.
    """
    from utils.logger import get_logger

    return get_logger(name)

def ensure_file(path: Path) -> None:
    """Raise a clear error if ``path`` does not exist."""
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")

# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------
def load_eligible_subjects() -> pd.DataFrame:
    """Load the CSV produced by ``01_download_and_filter.py``.

    Expected columns (at minimum):
        - ``subject_id`` (string)
        - ``baseline_mmse`` (float)
        - ``followup_mmse`` (float)

    The decline label is computed as a drop of ≥ 3 points in MMSE.
    """
    csv_path = Path("data/processed/eligible_subjects.csv")
    ensure_file(csv_path)
    df = pd.read_csv(csv_path, dtype=str)

    # Ensure required columns exist; if not, raise early.
    required = {"subject_id", "baseline_mmse", "followup_mmse"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"eligible_subjects.csv missing columns: {missing}")

    # Convert scores to numeric (allow NaNs)
    df["baseline_mmse"] = pd.to_numeric(df["baseline_mmse"], errors="coerce")
    df["followup_mmse"] = pd.to_numeric(df["followup_mmse"], errors="coerce")
    return df

def load_features() -> pd.DataFrame:
    """Load the graph metrics CSV produced by ``03_compute_graph_metrics.py``."""
    csv_path = Path("data/processed/graph_metrics.csv")
    ensure_file(csv_path)
    df = pd.read_csv(csv_path, dtype=str)

    # Expected first column to be ``subject_id``; keep everything else as features.
    if "subject_id" not in df.columns:
        raise ValueError("graph_metrics.csv must contain a 'subject_id' column")
    # Convert all metric columns to numeric where possible.
    metric_cols = [c for c in df.columns if c != "subject_id"]
    df[metric_cols] = df[metric_cols].apply(pd.to_numeric, errors="coerce")
    return df

def split_features_labels(
    subjects_df: pd.DataFrame, features_df: pd.DataFrame
) -> Tuple[np.ndarray, np.ndarray]:
    """Merge subjects and features, then return ``X`` and ``y``.

    The label ``y`` is a binary indicator of cognitive decline:
    ``1`` if ``followup_mmse - baseline_mmse <= -3``, otherwise ``0``.
    """
    merged = pd.merge(
        subjects_df, features_df, on="subject_id", how="inner", validate="one_to_one"
    )
    # Compute decline label
    merged["decline"] = (
        merged["followup_mmse"] - merged["baseline_mmse"]
    ).apply(lambda d: 1 if d <= -3 else 0)

    # Drop any rows where scores are NaN (should not happen after filtering)
    merged = merged.dropna(subset=["decline"])

    y = merged["decline"].values.astype(int)
    X = merged.drop(columns=["subject_id", "baseline_mmse", "followup_mmse", "decline"]).values
    return X, y

def load_trained_model() -> Any:
    """Load the pickled model produced by ``04_train_model.py``."""
    pkl_path = Path("data/processed/model.pkl")
    ensure_file(pkl_path)
    model = load(pkl_path)
    return model

# ----------------------------------------------------------------------
# Metric helpers
# ----------------------------------------------------------------------
def isnan(x: Any) -> bool:
    """Return True if ``x`` is NaN (covers float, np.ndarray, pandas scalar)."""
    try:
        return np.isnan(x)
    except Exception:
        return False

def calculate_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray | None = None
) -> Dict[str, float]:
    """Return ROC‑AUC, accuracy and F1‑score.

    ``y_proba`` is expected to be the probability of the positive class.
    If ``y_proba`` is ``None`` the ROC‑AUC is set to ``np.nan``.
    """
    metrics: Dict[str, float] = {}

    if y_proba is not None and not isnan(y_proba).any():
        try:
            roc = roc_auc_score(y_true, y_proba[:, 1])
        except Exception:
            roc = np.nan
    else:
        roc = np.nan
    metrics["roc_auc"] = float(roc)

    metrics["accuracy"] = float(accuracy_score(y_true, y_pred))
    metrics["f1_score"] = float(f1_score(y_true, y_pred, zero_division=0))
    return metrics

# ----------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------
def write_performance_report(report: Dict[str, Any]) -> None:
    """Write ``report`` to ``data/processed/performance_report.json``."""
    out_path = Path("data/processed/performance_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

# ----------------------------------------------------------------------
# Main evaluation routine
# ----------------------------------------------------------------------
def evaluate_model(
    n_splits: int = 5, random_state: int = 42
) -> Dict[str, Any]:
    """Perform stratified K‑fold evaluation and return a report dict.

    The report contains:
        - ``folds``: a list of per‑fold metric dictionaries
        - ``mean``: a dictionary with the mean of each metric across folds
    """
    logger = get_logger_wrapper()
    logger.log("evaluation_start", n_splits=n_splits, random_state=random_state)

    subjects_df = load_eligible_subjects()
    features_df = load_features()
    X, y = split_features_labels(subjects_df, features_df)

    base_model = load_trained_model()
    # Ensure we work with a fresh, unfitted estimator each fold.
    # ``clone`` copies hyper‑parameters but not learned state.
    folds_metrics: List[Dict[str, float]] = []

    skf = StratifiedKFold(
        n_splits=n_splits, shuffle=True, random_state=random_state
    )
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y), start=1):
        logger.log(
            "fold_start",
            fold=fold_idx,
            train_size=len(train_idx),
            test_size=len(test_idx),
        )
        model_clone = clone(base_model)

        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model_clone.fit(X_train, y_train)

        # Predict probabilities if the estimator supports it
        if hasattr(model_clone, "predict_proba"):
            y_proba = model_clone.predict_proba(X_test)
        else:
            y_proba = None

        y_pred = model_clone.predict(X_test)

        metrics = calculate_metrics(y_test, y_pred, y_proba)
        metrics["fold"] = fold_idx
        folds_metrics.append(metrics)

        logger.log("fold_end", fold=fold_idx, **metrics)

    # Compute mean metrics (ignoring the ``fold`` key)
    mean_metrics = {
        "roc_auc": np.mean([m["roc_auc"] for m in folds_metrics if not np.isnan(m["roc_auc"])]),
        "accuracy": np.mean([m["accuracy"] for m in folds_metrics]),
        "f1_score": np.mean([m["f1_score"] for m in folds_metrics]),
    }
    return report

    report = {"folds": folds_metrics, "mean": mean_metrics}
    write_performance_report(report)

    logger.log("evaluation_complete", **report)
    return report

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Entry point for ``python code/05_evaluate_model.py``."""
    try:
        evaluate_model()
    except Exception as exc:
        logger = get_logger_wrapper()
        logger.log("evaluation_error", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()