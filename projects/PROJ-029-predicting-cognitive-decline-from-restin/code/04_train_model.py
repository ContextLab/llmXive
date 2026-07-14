"""Train a Random Forest model with nested cross‑validation.

This script implements the full training pipeline required by task T023.
It:
  * Loads graph‑metric features (data/processed/graph_metrics.csv)
  * Loads eligible subject metadata (data/processed/eligible_subjects.csv)
  * Defines a binary decline label (drop ≥ 3 points in MMSE or MoCA)
  * Performs a nested 5‑fold outer CV with an inner grid‑search over
    `n_estimators ∈ {50, 100, 200}` and `max_depth ∈ {5, 10, None}`.
  * Within each inner CV loop it:
      - Removes collinear features (|r| > 0.95, keeping the higher‑variance one)
      - Applies a variance‑threshold (threshold = 0.01)
      - Runs Recursive Feature Elimination (RFE) to keep ≤ 20 features
  * Fits a RandomForestClassifier with the selected hyper‑parameters.
  * Saves the best‑overall model to `data/processed/model.pkl`.
  * Writes a performance summary (`roc_auc`, `accuracy`, `f1`) to
    `data/processed/performance_report.json`.

All logging is performed via the tolerant logger in ``utils.logger``.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline

from utils.logger import get_logger, log_operation

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

LOGGER = get_logger("04_train_model")


def load_features() -> pd.DataFrame:
    """Load graph‑metric features.

    Returns a DataFrame with ``subject_id`` as the first column and all
    metric columns following it.
    """
    features_path = Path("data/processed/graph_metrics.csv")
    if not features_path.is_file():
        LOGGER.error(f"Feature file not found: {features_path}")
        sys.exit(1)
    df = pd.read_csv(features_path)
    LOGGER.info("Loaded features", path=str(features_path), rows=df.shape[0])
    return df


def load_eligible_subjects() -> pd.DataFrame:
    """Load the CSV produced by ``01_download_and_filter``."""
    subjects_path = Path("data/processed/eligible_subjects.csv")
    if not subjects_path.is_file():
        LOGGER.error(f"Eligible subjects file not found: {subjects_path}")
        sys.exit(1)
    df = pd.read_csv(subjects_path)
    LOGGER.info("Loaded eligible subjects", path=str(subjects_path), rows=df.shape[0])
    return df


def define_decline_label(df: pd.DataFrame) -> pd.Series:
    """
    Define a binary decline label.

    The label is ``1`` if **either** MMSE or MoCA drops by 3 or more points
    between the two timepoints; otherwise ``0``.

    Expected columns in ``df``:
      * ``baseline_mmse``, ``followup_mmse``,
      * ``baseline_moca``, ``followup_moca``.
    """
    required = {
        "baseline_mmse",
        "followup_mmse",
        "baseline_moca",
        "followup_moca",
    }
    missing = required - set(df.columns)
    if missing:
        LOGGER.error("Missing columns for label definition", missing=list(missing))
        sys.exit(1)

    mmse_drop = df["baseline_mmse"] - df["followup_mmse"]
    moca_drop = df["baseline_moca"] - df["followup_moca"]
    label = ((mmse_drop >= 3) | (moca_drop >= 3)).astype(int)
    LOGGER.info("Defined decline label", positive=int(label.sum()), total=len(label))
    return label

# --------------------------------------------------------------------------- #
# Feature‑selection transformers
# --------------------------------------------------------------------------- #


class CollinearityTransformer:
    """
    Drop one feature from each pair whose absolute Pearson correlation exceeds 0.95.

    The feature with the **higher variance** is retained.
    """

    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.to_drop_: list[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "CollinearityTransformer":
        corr = X.corr().abs()
        # Upper triangle without diagonal
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))

        for col in upper.columns:
            high_corr = upper[col][upper[col] > self.threshold].index.tolist()
            for other in high_corr:
                # Decide which to drop based on variance
                var_col = X[col].var()
                var_other = X[other].var()
                if var_col >= var_other:
                    self.to_drop_.append(other)
                else:
                    self.to_drop_.append(col)
        # Ensure uniqueness
        self.to_drop_ = list(set(self.to_drop_))
        LOGGER.info("Collinearity transformer fitted", drop_count=len(self.to_drop_))
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.to_drop_:
            return X.copy()
        LOGGER.debug("Dropping collinear features", features=self.to_drop_)
        return X.drop(columns=self.to_drop_, errors="ignore")

    def fit_transform(self, X: pd.DataFrame, y: pd.Series | None = None) -> pd.DataFrame:
        return self.fit(X, y).transform(X)

# --------------------------------------------------------------------------- #
# Pipeline construction
# --------------------------------------------------------------------------- #


def make_inner_pipeline() -> Pipeline:
    """
    Build the inner pipeline that will be used inside GridSearchCV.

    Steps:
      1. Collinearity removal
      2. Variance thresholding (threshold=0.01)
      3. RFE (max 20 features)
      4. RandomForest classifier (parameters will be set by GridSearch)
    """
    pipeline = Pipeline(
        [
            ("collinearity", CollinearityTransformer()),
            ("var_thresh", VarianceThreshold(threshold=0.01)),
            (
                "rfe",
                RFE(
                    estimator=RandomForestClassifier(random_state=42, n_jobs=1),
                    n_features_to_select=20,
                ),
            ),
            ("clf", RandomForestClassifier(random_state=42, n_jobs=1)),
        ]
    )
    LOGGER.info("Constructed inner pipeline")
    return pipeline

# --------------------------------------------------------------------------- #
# Nested CV training
# --------------------------------------------------------------------------- #


def train_and_evaluate_nested_cv(
    X: pd.DataFrame,
    y: pd.Series,
    outer_folds: int = 5,
) -> dict:
    """
    Perform nested cross‑validation.

    Returns a dictionary containing mean metrics and the best estimator
    trained on the full dataset.
    """
    outer_cv = StratifiedKFold(n_splits=outer_folds, shuffle=True, random_state=42)

    # Parameter grid as required by FR‑003
    param_grid = {
        "clf__n_estimators": [50, 100, 200],
        "clf__max_depth": [5, 10, None],
    }

    # Containers for metrics
    aucs: list[float] = []
    accs: list[float] = []
    f1s: list[float] = []

    # Store the best inner model (by mean CV score) to refit on the whole data later
    best_score = -np.inf
    best_params = None

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y), start=1):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=fold_idx)
        pipeline = make_inner_pipeline()

        grid = GridSearchCV(
            estimator=pipeline,
            param_grid=param_grid,
            cv=inner_cv,
            scoring="roc_auc",
            n_jobs=2,
            verbose=0,
        )

        LOGGER.info("Starting inner grid‑search", outer_fold=fold_idx)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            grid.fit(X_train, y_train)

        # Evaluate on outer test set
        y_pred_proba = grid.predict_proba(X_test)[:, 1]
        y_pred = grid.predict(X_test)

        auc = roc_auc_score(y_test, y_pred_proba)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        aucs.append(auc)
        accs.append(acc)
        f1s.append(f1)

        LOGGER.info(
            "Outer fold results",
            fold=fold_idx,
            roc_auc=auc,
            accuracy=acc,
            f1=f1,
        )

        # Track best inner model
        if grid.best_score_ > best_score:
            best_score = grid.best_score_
            best_params = grid.best_params_
            best_estimator = grid.best_estimator_

    # Re‑fit best estimator on the full dataset
    LOGGER.info("Refitting best estimator on full data", best_score=best_score)
    best_estimator.fit(X, y)

    # Persist the model
    model_path = Path("data/processed/model.pkl")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_estimator, model_path)
    LOGGER.info("Saved trained model", path=str(model_path))

    # Prepare performance report
    report = {
        "mean_roc_auc": float(np.mean(aucs)),
        "mean_accuracy": float(np.mean(accs)),
        "mean_f1": float(np.mean(f1s)),
        "outer_folds": outer_folds,
        "best_inner_params": best_params,
    }

    report_path = Path("data/processed/performance_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w") as f:
        json.dump(report, f, indent=2)
    LOGGER.info("Wrote performance report", path=str(report_path))

    return {
        "mean_roc_auc": report["mean_roc_auc"],
        "mean_accuracy": report["mean_accuracy"],
        "mean_f1": report["mean_f1"],
        "best_params": best_params,
    }

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #


def main() -> int:
    """
    Execute the training pipeline.

    Returns exit code 0 on success, non‑zero otherwise.
    """
    try:
        # Load data
        features_df = load_features()
        subjects_df = load_eligible_subjects()

        # Merge on subject_id
        merged = pd.merge(
            subjects_df,
            features_df,
            on="subject_id",
            how="inner",
        )
        if merged.empty:
            LOGGER.error("No overlapping subjects between metadata and features")
            return 1

        # Define label
        y = define_decline_label(merged)

        # Features (drop non‑metric columns)
        X = merged.drop(columns=["subject_id", "baseline_mmse", "followup_mmse", "baseline_moca", "followup_moca"])

        # Ensure X is a DataFrame (some callers expect a DataFrame)
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        # Train & evaluate
        results = train_and_evaluate_nested_cv(X, y)

        LOGGER.info("Training completed", results=results)
        return 0
    except Exception as exc:  # pragma: no cover – defensive
        LOGGER.error("Unhandled exception in training", error=str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
