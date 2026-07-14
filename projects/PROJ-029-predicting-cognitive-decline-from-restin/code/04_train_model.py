"""Training script for predicting cognitive decline from rs‑fMRI graph metrics.

This module implements the full nested‑cross‑validation pipeline required by
task **T023**.  It:

1. Loads graph‑metric features from ``data/processed/graph_metrics.csv``.
2. Loads the list of eligible subjects (with baseline & follow‑up scores)
   from ``data/processed/eligible_subjects.csv``.
3. Derives a binary decline label (drop ≥ 3 points on MMSE/MoCA).
4. Performs a 5‑fold outer CV.  Within each outer training split a grid‑search
   inner CV (3‑fold) optimises ``n_estimators`` and ``max_depth`` of a
   ``RandomForestClassifier`` while applying:
      * Collinearity filtering (Pearson > 0.95, keep higher‑variance feature)
      * Variance‑thresholding (variance > 0.01)
      * Recursive feature elimination (≤ 20 features)
5. Persists the best model to ``data/processed/model.pkl``.
6. Writes a performance report (mean ROC‑AUC, per‑fold scores, best hyper‑params)
   to ``data/processed/performance_report.json``.

All logging is performed via the tolerant ``utils.logger`` implementation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline

from utils.logger import get_logger, log_operation

# --------------------------------------------------------------------------- #
# Logging setup
# --------------------------------------------------------------------------- #
LOGGER = get_logger("04_train_model")

# --------------------------------------------------------------------------- #
# Helper / utility classes
# --------------------------------------------------------------------------- #

class CollinearityTransformer(BaseEstimator, TransformerMixin):
    """Remove one feature from each pair with Pearson correlation > threshold.

    The feature with the lower variance is dropped.  This transformer is
    stateless after ``fit`` – it records the indices to keep and applies the
    same mask during ``transform``.
    """

    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self._keep_mask: np.ndarray | None = None

    def fit(self, X: pd.DataFrame, y=None):
        corr = X.corr().abs()
        # Upper triangle, without diagonal
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        to_drop = set()
        variances = X.var()

        for col in upper.columns:
            for row in upper.index:
                if pd.isna(upper.at[row, col]):
                    continue
                if upper.at[row, col] > self.threshold:
                    # Drop the lower‑variance feature
                    if variances[col] < variances[row]:
                        to_drop.add(col)
                    else:
                        to_drop.add(row)
        keep = [i for i, col in enumerate(X.columns) if col not in to_drop]
        self._keep_mask = np.array(keep, dtype=int)
        return self

    def transform(self, X: pd.DataFrame):
        if self._keep_mask is None:
            raise RuntimeError("CollinearityTransformer not fitted")
        return X.iloc[:, self._keep_mask]

    def get_feature_names_out(self, input_features=None):
        if self._keep_mask is None:
            raise RuntimeError("CollinearityTransformer not fitted")
        return [input_features[i] for i in self._keep_mask] if input_features is not None else None

# --------------------------------------------------------------------------- #
# Data loading utilities
# --------------------------------------------------------------------------- #

def load_features() -> pd.DataFrame:
    """Load graph‑metric features."""
    features_path = Path("data/processed/graph_metrics.csv")
    if not features_path.is_file():
        LOGGER.error(f"Feature file not found at {features_path}")
        raise FileNotFoundError(features_path)
    df = pd.read_csv(features_path)
    LOGGER.info(f"Loaded features with shape {df.shape}")
    return df

def load_eligible_subjects() -> pd.DataFrame:
    """Load the CSV produced by ``01_download_and_filter.py``."""
    path = Path("data/processed/eligible_subjects.csv")
    if not path.is_file():
        LOGGER.error(f"Eligible subjects file not found at {path}")
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    LOGGER.info(f"Loaded eligible subjects with shape {df.shape}")
    return df

# --------------------------------------------------------------------------- #
# Label definition
# --------------------------------------------------------------------------- #

def define_decline_label(df: pd.DataFrame) -> pd.Series:
    """Create a binary decline label (drop ≥ 3 points).

    The input DataFrame must contain either:
    * ``mmse_baseline`` and ``mmse_followup`` columns, **or**
    * ``moca_baseline`` and ``moca_followup`` columns.
    Preference is given to MMSE if both are present.
    """
    if {"mmse_baseline", "mmse_followup"}.issubset(df.columns):
        delta = df["mmse_baseline"] - df["mmse_followup"]
    elif {"moca_baseline", "moca_followup"}.issubset(df.columns):
        delta = df["moca_baseline"] - df["moca_followup"]
    else:
        raise ValueError("No suitable cognitive score columns found for label creation.")
    label = (delta >= 3).astype(int)
    LOGGER.info(f"Defined decline label: {label.sum()} positives out of {len(label)}")
    return label

# --------------------------------------------------------------------------- #
# Pipeline construction
# --------------------------------------------------------------------------- #

def make_inner_pipeline() -> Pipeline:
    """Construct the inner preprocessing + classifier pipeline."""
    pipeline = Pipeline(
        steps=[
            ("collinearity", CollinearityTransformer(threshold=0.95)),
            ("variance", VarianceThreshold(threshold=0.01)),
            ("rfe", RFE(
                estimator=RandomForestClassifier(random_state=42, n_jobs=1),
                n_features_to_select=20,
                step=1
            )),
            ("clf", RandomForestClassifier(random_state=42, n_jobs=1))
        ]
    )
    return pipeline

# --------------------------------------------------------------------------- #
# Model training / evaluation
# --------------------------------------------------------------------------- #

def train_and_evaluate_nested_cv(
    X: pd.DataFrame,
    y: pd.Series,
) -> Tuple[Pipeline, dict]:
    """Run a 5‑fold outer CV with inner grid‑search.

    Returns the best pipeline (refitted on the whole dataset) and a report
    dictionary containing per‑fold ROC‑AUC scores and the best hyper‑parameters.
    """
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

    param_grid = {
        "clf__n_estimators": [50, 100, 200],
        "clf__max_depth": [5, 10, None],
    }

    outer_scores = []
    best_params_across_folds = []
    best_estimators = []

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y), start=1):
        LOGGER.info(f"Starting outer fold {fold_idx}")
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        pipeline = make_inner_pipeline()
        grid = GridSearchCV(
            estimator=pipeline,
            param_grid=param_grid,
            cv=inner_cv,
            scoring="roc_auc",
            n_jobs=2,
            refit=True,
        )

        grid.fit(X_train, y_train)
        best_params_across_folds.append(grid.best_params_)

        # Predict probabilities for the positive class
        probas = grid.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, probas)
        outer_scores.append(auc)
        LOGGER.info(f"Outer fold {fold_idx} ROC‑AUC: {auc:.4f}")

        # Store the fitted estimator for potential later analysis
        best_estimators.append(grid.best_estimator_)

    # Re‑fit on the full dataset using the most frequently selected hyper‑params
    # (simple majority vote). If a tie, the first encountered wins.
    from collections import Counter

    most_common_params = Counter(tuple(sorted(p.items())) for p in best_params_across_folds).most_common(1)[0][0]
    best_params = dict(most_common_params)
    LOGGER.info(f"Most common hyper‑parameters across folds: {best_params}")

    final_pipeline = make_inner_pipeline()
    final_pipeline.set_params(**{
        f"clf__{k}": v for k, v in best_params.items()
    })
    final_pipeline.fit(X, y)

    report = {
        "outer_fold_roc_auc": outer_scores,
        "mean_roc_auc": float(np.mean(outer_scores)),
        "best_params": best_params,
    }
    return final_pipeline, report

# --------------------------------------------------------------------------- #
# Persistence helpers
# --------------------------------------------------------------------------- #

def persist_model(pipeline: Pipeline) -> None:
    """Save the trained pipeline to disk."""
    model_path = Path("data/processed/model.pkl")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    LOGGER.info(f"Model persisted to {model_path}")

def write_performance_report(report: dict) -> None:
    """Write the performance JSON report."""
    report_path = Path("data/processed/performance_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    LOGGER.info(f"Performance report written to {report_path}")

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

@log_operation("train_model")
def main() -> int:
    try:
        features_df = load_features()
        subjects_df = load_eligible_subjects()

        # Align features with subjects – assume ``subject_id`` column exists in both.
        if "subject_id" not in features_df.columns or "subject_id" not in subjects_df.columns:
            LOGGER.error("Both feature and subject tables must contain a 'subject_id' column.")
            return 1

        merged = pd.merge(subjects_df, features_df, on="subject_id", how="inner")
        if merged.empty:
            LOGGER.error("No overlapping subject IDs between features and eligible subjects.")
            return 1

        y = define_decline_label(merged)
        # Drop non‑feature columns (subject_id and any score columns)
        feature_cols = [c for c in merged.columns if c not in {"subject_id", "mmse_baseline", "mmse_followup", "moca_baseline", "moca_followup"}]
        X = merged[feature_cols]

        LOGGER.info(f"Starting nested CV with {X.shape[0]} samples and {X.shape[1]} features.")

        best_pipeline, report = train_and_evaluate_nested_cv(X, y)

        persist_model(best_pipeline)
        write_performance_report(report)

        # Log final selected hyper‑parameters for audit (FR‑003 compliance)
        LOGGER.info(f"Final model hyper‑parameters: {report['best_params']}")

        return 0
    except Exception as exc:
        LOGGER.error(f"Training failed: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())