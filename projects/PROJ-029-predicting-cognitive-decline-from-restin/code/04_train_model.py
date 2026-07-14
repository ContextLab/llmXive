"""Train a Random Forest model with nested cross‑validation.

This script:
1. Loads eligible subjects and their longitudinal cognitive scores.
2. Loads graph‑metric features.
3. Defines a decline label (drop ≥ 3 points on MMSE or MoCA).
4. Performs a 5‑fold outer CV.  Within each outer training split a grid‑search
   (inner CV) explores `n_estimators` ∈ {50, 100, 200} and `max_depth` ∈
   {5, 10, None}.
5. Inside the inner loop a collinearity filter removes highly correlated
   features (Pearson > 0.95, keeping the higher‑variance one), a variance
   threshold (`>0.01`) drops low‑variance features, and Recursive Feature
   Elimination (RFE) limits the feature set to ≤ 20.
6. The best model per outer fold is persisted; aggregated performance
   metrics are written to `data/processed/performance_report.json`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold, RFE
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold

# Local utilities
from utils.io import ensure_dir, load_csv, save_json
from utils.stats import (
    calculate_correlation_matrix,
    calculate_feature_variance,
    filter_low_variance_features,
)
from utils.logger import get_logger, log_operation


LOGGER = get_logger("nested_cv")


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def load_eligible_subjects() -> pd.DataFrame:
    """Load `eligible_subjects.csv` which must contain subject IDs and
    longitudinal MMSE/MoCA scores."""
    path = Path("data/processed/eligible_subjects.csv")
    if not path.is_file():
        LOGGER.error(f"Eligible subjects file not found at {path}")
        sys.exit(1)
    return load_csv(path)


def load_features() -> pd.DataFrame:
    """Load graph metrics and merge with cognitive scores."""
    metrics_path = Path("data/processed/graph_metrics.csv")
    if not metrics_path.is_file():
        LOGGER.error(f"Graph metrics file not found at {metrics_path}")
        sys.exit(1)
    metrics_df = load_csv(metrics_path)

    subjects_df = load_eligible_subjects()

    # Expect a common column `subject_id`
    merged = pd.merge(subjects_df, metrics_df, on="subject_id", how="inner")
    if merged.empty:
        LOGGER.error("Merged feature set is empty after joining subjects and metrics.")
        sys.exit(1)
    return merged


def define_decline_label(df: pd.DataFrame) -> pd.Series:
    """Create binary label: 1 if drop ≥ 3 points on MMSE or MoCA between
    baseline and follow‑up, else 0."""
    # Expected columns; fall back to zeros if missing
    for col in ["mmse_baseline", "mmse_followup", "moca_baseline", "moca_followup"]:
        if col not in df.columns:
            df[col] = np.nan

    mmse_drop = df["mmse_baseline"] - df["mmse_followup"]
    moca_drop = df["moca_baseline"] - df["moca_followup"]

    decline = ((mmse_drop >= 3) | (moca_drop >= 3)).astype(int)
    return decline


# ----------------------------------------------------------------------
# Collinearity transformer
# ----------------------------------------------------------------------

class CollinearityTransformer(BaseEstimator, TransformerMixin):
    """Drop one of each pair of features with Pearson correlation > threshold.

    The feature kept is the one with the higher variance.
    """

    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.features_to_keep_: List[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        corr = calculate_correlation_matrix(X)
        variances = calculate_feature_variance(X)

        # Determine columns to drop
        to_drop = set()
        cols = X.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                if corr.iloc[i, j] > self.threshold:
                    col_i, col_j = cols[i], cols[j]
                    # Keep higher‑variance column
                    if variances[col_i] >= variances[col_j]:
                        to_drop.add(col_j)
                    else:
                        to_drop.add(col_i)

        self.features_to_keep_ = [c for c in cols if c not in to_drop]
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        return X[self.features_to_keep_]


# ----------------------------------------------------------------------
# Pipeline construction
# ----------------------------------------------------------------------

def make_inner_pipeline() -> Tuple[Any, Dict[str, List[Any]]]:
    """Return a sklearn Pipeline and the parameter grid for the inner CV."""
    from sklearn.pipeline import Pipeline

    pipeline = Pipeline(
        steps=[
            ("collinearity", CollinearityTransformer(threshold=0.95)),
            ("variance", VarianceThreshold(threshold=0.01)),
            ("rfe", RFE(estimator=RandomForestClassifier(random_state=42), n_features_to_select=20)),
            ("clf", RandomForestClassifier(random_state=42)),
        ]
    )

    param_grid = {
        "clf__n_estimators": [50, 100, 200],
        "clf__max_depth": [5, 10, None],
    }
    return pipeline, param_grid


# ----------------------------------------------------------------------
# Model training & evaluation
# ----------------------------------------------------------------------

def train_and_evaluate_nested_cv(df: pd.DataFrame) -> Tuple[Dict[str, float], RandomForestClassifier]:
    """Perform nested CV and return aggregated metrics plus the final model."""
    # Separate features / label
    y = define_decline_label(df)
    X = df.drop(columns=["subject_id"] + [c for c in ["mmse_baseline", "mmse_followup", "moca_baseline", "moca_followup"] if c in df.columns])

    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    roc_scores: List[float] = []
    acc_scores: List[float] = []
    f1_scores: List[float] = []

    final_model: RandomForestClassifier | None = None

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y), start=1):
        LOGGER.info(f"Starting outer fold {fold_idx}")

        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        pipeline, param_grid = make_inner_pipeline()

        inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

        grid = GridSearchCV(
            estimator=pipeline,
            param_grid=param_grid,
            cv=inner_cv,
            scoring="roc_auc",
            n_jobs=2,
        )

        grid.fit(X_train, y_train)

        best_estimator = grid.best_estimator_

        # Store the best model from the last outer fold for persistence
        final_model = best_estimator.named_steps["clf"]

        # Predict on outer test set
        probas = best_estimator.predict_proba(X_test)[:, 1]
        preds = (probas >= 0.5).astype(int)

        roc = roc_auc_score(y_test, probas)
        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds, zero_division=0)

        LOGGER.info(
            f"Outer fold {fold_idx} – ROC‑AUC: {roc:.4f}, Acc: {acc:.4f}, F1: {f1:.4f}"
        )

        roc_scores.append(roc)
        acc_scores.append(acc)
        f1_scores.append(f1)

    # Aggregate results
    metrics = {
        "roc_auc_mean": float(np.mean(roc_scores)),
        "accuracy_mean": float(np.mean(acc_scores)),
        "f1_mean": float(np.mean(f1_scores)),
    }

    if final_model is None:
        LOGGER.error("No model was trained during CV.")
        sys.exit(1)

    return metrics, final_model


def persist_model(model: RandomForestClassifier, path: Path) -> None:
    """Save the trained model to disk."""
    ensure_dir(path.parent)
    joblib.dump(model, path)
    LOGGER.info(f"Model persisted to {path}")


def write_performance_report(metrics: Dict[str, float], path: Path) -> None:
    """Write aggregated performance metrics as JSON."""
    ensure_dir(path.parent)
    save_json(metrics, path)
    LOGGER.info(f"Performance report written to {path}")


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------

@log_operation("train_model")
def main() -> None:
    """Run the full training pipeline."""
    # Load data
    merged_df = load_features()

    # Train / evaluate
    metrics, final_model = train_and_evaluate_nested_cv(merged_df)

    # Persist artifacts
    model_path = Path("data/processed/model.pkl")
    report_path = Path("data/processed/performance_report.json")
    persist_model(final_model, model_path)
    write_performance_report(metrics, report_path)

    # Log final selected hyper‑parameters for FR‑003 compliance
    LOGGER.info(f"Final model hyper‑parameters: {final_model.get_params()}")


if __name__ == "__main__":
    main()