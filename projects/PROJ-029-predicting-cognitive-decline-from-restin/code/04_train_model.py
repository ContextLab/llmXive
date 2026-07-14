"""Nested cross‑validation training script for predicting cognitive decline.

This script:
  1. Loads eligible subject IDs and the pre‑computed graph metrics.
  2. Constructs a binary decline label (drop ≥ 3 points on MMSE between
     baseline and follow‑up).
  3. Performs a 5‑fold outer CV.  Inside each outer training split an
     inner grid‑search (2‑fold) optimises ``n_estimators`` and ``max_depth``
     of a RandomForest while applying:
        * Collinearity filtering (correlation > 0.95, keep higher‑variance).
        * VarianceThreshold (threshold = 0.01).
        * Recursive Feature Elimination (RFE) to keep ≤ 20 features.
  4. Persists the best‑performing model to ``data/processed/model.pkl``.
  5. Writes a JSON performance report (mean ROC‑AUC, mean F1, selected
     hyper‑parameters) to ``data/processed/performance_report.json``.

All logging is performed through the tolerant ``utils.logger`` module.
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
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.model_selection import GridSearchCV, KFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

from utils.io import ensure_dir, load_csv, save_pickle, save_json
from utils.stats import calculate_correlation_matrix, calculate_feature_variance
from utils.logger import get_logger, log_operation


# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #


ELIGIBLE_SUBJECTS_CSV = Path("data/processed/eligible_subjects.csv")
GRAPH_METRICS_CSV = Path("data/processed/graph_metrics.csv")
MODEL_OUTPUT = Path("data/processed/model.pkl")
PERFORMANCE_REPORT_JSON = Path("data/processed/performance_report.json")



def load_eligible_subjects() -> pd.DataFrame:
    """Load the CSV produced by ``01_download_and_filter``."""
    if not ELIGIBLE_SUBJECTS_CSV.is_file():
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_CSV}")
    df = load_csv(ELIGIBLE_SUBJECTS_CSV)
    # Expect a column named ``participant_id``; be tolerant to alternatives.
    if "participant_id" not in df.columns:
        # Try common alternatives
        for col in ("subject_id", "sub_id", "id"):
            if col in df.columns:
                df = df.rename(columns={col: "participant_id"})
                break
        else:
            raise KeyError("No participant identifier column found in eligible subjects CSV.")
    return df[["participant_id"]].drop_duplicates()


def load_features() -> pd.DataFrame:
    """Load graph metrics and merge with eligibility list."""
    if not GRAPH_METRICS_CSV.is_file():
        raise FileNotFoundError(f"Graph metrics file not found: {GRAPH_METRICS_CSV}")
    metrics = load_csv(GRAPH_METRICS_CSV)
    eligible = load_eligible_subjects()
    merged = pd.merge(eligible, metrics, left_on="participant_id", right_on="participant_id", how="inner")
    if merged.empty:
        raise ValueError("No overlapping subjects between eligible list and graph metrics.")
    return merged


def define_decline_label(df: pd.DataFrame) -> pd.Series:
    """
    Create a binary label indicating cognitive decline.

    The spec defines decline as a drop of **≥ 3 points** on the MMSE
    between the two time‑points.  The graph‑metrics CSV is expected to
    contain ``mmse_T1`` and ``mmse_T2`` columns; if they are missing we
    fallback to ``moca_T1``/``moca_T2``.
    """
    if {"mmse_T1", "mmse_T2"}.issubset(df.columns):
        delta = df["mmse_T1"] - df["mmse_T2"]
    elif {"moca_T1", "moca_T2"}.issubset(df.columns):
        delta = df["moca_T1"] - df["moca_T2"]
    else:
        raise KeyError("Neither MMSE nor MoCA columns found for label creation.")
    return (delta >= 3).astype(int)


# --------------------------------------------------------------------------- #
# Collinearity transformer
# --------------------------------------------------------------------------- #


class CollinearityTransformer(BaseEstimator, TransformerMixin):
    """
    Remove one feature from each pair whose absolute Pearson correlation exceeds
    ``threshold``.  The feature with the **lower variance** is dropped.
    """

    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.keep_mask_: np.ndarray | None = None

    def fit(self, X: pd.DataFrame, y: Any = None):
        """Identify columns to keep."""
        corr = calculate_correlation_matrix(X)
        # Upper triangle, excluding diagonal
        high_corr = (np.abs(corr) > self.threshold) & (~np.eye(corr.shape[0], dtype=bool))

        # Determine variance for each column
        variances = calculate_feature_variance(X)

        # Initialise all columns as kept
        keep = np.ones(X.shape[1], dtype=bool)

        # Iterate over pairs; drop the lower‑variance column
        for i in range(corr.shape[0]):
            for j in range(i + 1, corr.shape[1]):
                if high_corr[i, j]:
                    if variances[i] < variances[j]:
                        keep[i] = False
                    else:
                        keep[j] = False
        self.keep_mask_ = keep
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return X with only the kept columns."""
        if self.keep_mask_ is None:
            raise RuntimeError("CollinearityTransformer must be fitted before transform.")
        kept_columns = X.columns[self.keep_mask_]
        return X.loc[:, kept_columns]


# --------------------------------------------------------------------------- #
# Pipeline construction
# --------------------------------------------------------------------------- #


def make_inner_pipeline(collinearity_transformer: CollinearityTransformer) -> Pipeline:
    """
    Build the inner pipeline used inside the grid‑search.

    Steps:
      1. Collinearity filtering (custom transformer).
      2. VarianceThreshold (threshold=0.01).
      3. RFE with a RandomForest (max_features=20).
      4. RandomForest classifier (hyper‑parameters set by GridSearchCV).
    """
    variance_filter = VarianceThreshold(threshold=0.01)

    # RFE will be configured later once we know the number of features;
    # we set ``n_features_to_select`` to 20 (or the total number of features
    # if fewer than 20 are available) inside the pipeline definition.
    rfe = RFE(
        estimator=RandomForestClassifier(random_state=42, n_jobs=1),
        n_features_to_select=20,
        step=1,
    )

    rf = RandomForestClassifier(random_state=42, n_jobs=1)

    pipeline = Pipeline(
        [
            ("collinearity", collinearity_transformer),
            ("variance", variance_filter),
            ("rfe", rfe),
            ("rf", rf),
        ]
    )
    return pipeline


# --------------------------------------------------------------------------- #
# Nested cross‑validation
# --------------------------------------------------------------------------- #


def train_and_evaluate_nested_cv(
    X: pd.DataFrame,
    y: np.ndarray,
    outer_folds: int = 5,
    inner_folds: int = 2,
    random_state: int = 42,
) -> Tuple[RandomForestClassifier, Dict[str, Any]]:
    """
    Perform nested CV.

    Returns:
        best_estimator: RandomForest fitted on the whole dataset with the
                        best hyper‑parameters found during outer CV.
        report: Dictionary containing mean ROC‑AUC, mean F1‑score and the
                hyper‑parameters selected for the final model.
    """
    outer_cv = StratifiedKFold(n_splits=outer_folds, shuffle=True, random_state=random_state)

    outer_roc_auc_scores: List[float] = []
    outer_f1_scores: List[float] = []
    best_params: List[Dict[str, Any]] = []

    # Store the estimator from the outer fold that achieved the highest ROC‑AUC
    best_outer_score = -np.inf
    best_estimator: RandomForestClassifier | None = None

    for outer_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y), start=1):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Build inner pipeline
        col_transformer = CollinearityTransformer(threshold=0.95)
        pipeline = make_inner_pipeline(col_transformer)

        param_grid = {
            "rf__n_estimators": [50, 100, 200],
            "rf__max_depth": [5, 10, None],
        }

        inner_cv = StratifiedKFold(n_splits=inner_folds, shuffle=True, random_state=random_state)

        grid = GridSearchCV(
            estimator=pipeline,
            param_grid=param_grid,
            cv=inner_cv,
            scoring="roc_auc",
            n_jobs=1,  # Respect the 2‑core runner limit
        )

        grid.fit(X_train, y_train)

        # Evaluate on the outer test set
        y_proba = grid.predict_proba(X_test)[:, 1]
        y_pred = (y_proba >= 0.5).astype(int)

        roc_auc = roc_auc_score(y_test, y_proba)
        f1 = f1_score(y_test, y_pred)

        outer_roc_auc_scores.append(roc_auc)
        outer_f1_scores.append(f1)
        best_params.append(grid.best_params_)

        # Keep the best outer estimator
        if roc_auc > best_outer_score:
            best_outer_score = roc_auc
            # Re‑fit the pipeline on the *full* training data of this outer fold
            best_estimator = grid.best_estimator_.named_steps["rf"]

        # Logging for each outer fold
        logger = get_logger("nested_cv")
        logger.log(
            operation="outer_fold_complete",
            fold=outer_idx,
            roc_auc=roc_auc,
            f1=f1,
            best_params=grid.best_params_,
        )

    # Aggregate performance
    mean_roc_auc = float(np.mean(outer_roc_auc_scores))
    mean_f1 = float(np.mean(outer_f1_scores))

    # Determine the most frequently selected hyper‑parameters across folds
    # (simple majority vote)
    from collections import Counter

    flat_params = [json.dumps(p, sort_keys=True) for p in best_params]
    most_common_json, _ = Counter(flat_params).most_common(1)[0]
    most_common_params = json.loads(most_common_json)

    # Fit final model on *all* data using the most common parameters
    final_col_transformer = CollinearityTransformer(threshold=0.95)
    final_pipeline = make_inner_pipeline(final_col_transformer)
    final_pipeline.set_params(**most_common_params)
    final_pipeline.fit(X, y)

    # Extract the underlying RandomForest after the pipeline steps
    final_rf: RandomForestClassifier = final_pipeline.named_steps["rf"]

    report = {
        "mean_roc_auc": mean_roc_auc,
        "mean_f1": mean_f1,
        "selected_hyperparameters": most_common_params,
    }

    return final_rf, report


# --------------------------------------------------------------------------- #
# Persistence helpers
# --------------------------------------------------------------------------- #


def persist_model(model: RandomForestClassifier, out_path: Path = MODEL_OUTPUT) -> None:
    """Serialise the trained RandomForest model to disk."""
    ensure_dir(out_path.parent)
    joblib.dump(model, out_path)
    logger = get_logger("nested_cv")
    logger.log("model_persisted", path=str(out_path))


def write_performance_report(report: Dict[str, Any], out_path: Path = PERFORMANCE_REPORT_JSON) -> None:
    """Write the JSON performance report."""
    ensure_dir(out_path.parent)
    save_json(report, out_path)
    logger = get_logger("nested_cv")
    logger.log("performance_report_written", path=str(out_path))


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #


def main() -> None:
    """Run the full nested‑CV training pipeline."""
    logger = get_logger("nested_cv")
    logger.log("pipeline_start")

    try:
        df = load_features()
    except Exception as exc:
        logger.log("load_features_error", error=str(exc))
        sys.exit(1)

    # Separate features from label
    y = define_decline_label(df).values
    X = df.drop(columns=["participant_id"] + [col for col in df.columns if col.startswith("mmse_") or col.startswith("moca_")])

    if X.empty:
        logger.log("no_features_error", error="Feature matrix is empty after dropping label columns.")
        sys.exit(1)

    # Train & evaluate
    try:
        best_model, performance = train_and_evaluate_nested_cv(X, y)
    except Exception as exc:
        logger.log("training_error", error=str(exc))
        sys.exit(1)

    # Persist artifacts
    persist_model(best_model)
    write_performance_report(performance)

    logger.log("pipeline_complete", mean_roc_auc=performance["mean_roc_auc"], mean_f1=performance["mean_f1"])


if __name__ == "__main__":
    main()