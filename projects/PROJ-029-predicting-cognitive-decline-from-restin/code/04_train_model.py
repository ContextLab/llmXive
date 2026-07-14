"""Training script for predicting cognitive decline from resting‑state fMRI graph metrics."""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold, RFE
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline

from utils.logger import get_logger
from utils.io import ensure_dir

# ----------------------------------------------------------------------
# Configuration / paths
# ----------------------------------------------------------------------
LOGS_DIR = Path("data/artifacts")
MODEL_PATH = Path("data/processed/model.pkl")
FEATURES_PATH = Path("data/processed/graph_metrics.csv")
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")
TRAINING_PARAMS_PATH = Path("data/processed/training_params.json")

warnings.filterwarnings("ignore")


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def load_features() -> pd.DataFrame:
    """Load graph‑metric features. Must contain a ``subject_id`` column."""
    logger = get_logger("load_features")
    if not FEATURES_PATH.is_file():
        logger.error(f"Feature file not found: {FEATURES_PATH}")
        sys.exit(2)
    df = pd.read_csv(FEATURES_PATH)
    if "subject_id" not in df.columns:
        logger.error("Features CSV must contain a 'subject_id' column.")
        sys.exit(2)
    return df


def load_eligible_subjects() -> pd.DataFrame:
    """Load the CSV that lists subjects with longitudinal cognitive scores."""
    logger = get_logger("load_eligible_subjects")
    if not ELIGIBLE_SUBJECTS_PATH.is_file():
        logger.error(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")
        sys.exit(2)
    df = pd.read_csv(ELIGIBLE_SUBJECTS_PATH)
    if "subject_id" not in df.columns:
        logger.error("Eligible subjects CSV must contain a 'subject_id' column.")
        sys.exit(2)
    return df


def define_decline_label(subjects_df: pd.DataFrame) -> pd.Series:
    """
    Define the decline label.

    A subject is considered to have declined if the MMSE or MOCA score drops
    by **3 or more points** between the two time‑points. The function is tolerant
    to whichever score column(s) are present.
    """
    logger = get_logger("define_decline_label")
    # Expect columns like mmse_t1, mmse_t2, moca_t1, moca_t2
    decline = pd.Series(False, index=subjects_df.index)
    for prefix in ("mmse", "moca"):
        t1 = f"{prefix}_t1"
        t2 = f"{prefix}_t2"
        if t1 in subjects_df.columns and t2 in subjects_df.columns:
            diff = subjects_df[t2] - subjects_df[t1]
            decline = decline | (diff <= -3)
    if decline.sum() == 0:
        logger.warning("No subjects met the decline criterion.")
    return decline.astype(int)


# ----------------------------------------------------------------------
# Custom transformer for collinearity handling
# ----------------------------------------------------------------------
class CollinearityTransformer(BaseEstimator, TransformerMixin):
    """
    Drops one feature from each pair of highly correlated features
    (Pearson |r| > threshold). The feature with the higher variance is kept.
    """

    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self._keep_columns: Optional[List[str]] = None

    def fit(self, X: pd.DataFrame, y: Any = None):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        corr = X.corr().abs()
        # Upper triangle mask
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))

        to_drop = set()
        variances = X.var()

        for col in upper.columns:
            high_corr = [row for row in upper.index if upper.loc[row, col] > self.threshold]
            if high_corr:
                candidates = [col] + high_corr
                # Keep the one with the highest variance
                keep = max(candidates, key=lambda c: variances[c])
                drop = set(candidates) - {keep}
                to_drop.update(drop)

        self._keep_columns = [c for c in X.columns if c not in to_drop]
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if self._keep_columns is None:
            raise RuntimeError("CollinearityTransformer has not been fitted.")
        return X[self._keep_columns]


# ----------------------------------------------------------------------
# Pipeline construction
# ----------------------------------------------------------------------
def make_inner_pipeline() -> Pipeline:
    """
    Build the inner pipeline:
    1. Collinearity removal
    2. Variance thresholding (variance > 0.01)
    3. Recursive Feature Elimination (≤ 20 features)
    4. RandomForest classifier
    """
    steps = [
        ("collinearity", CollinearityTransformer()),
        ("variance", VarianceThreshold(threshold=0.01)),
        ("rfe", RFE(
            estimator=RandomForestClassifier(random_state=42, n_jobs=1),
            n_features_to_select=20,
            step=1)),
        ("clf", RandomForestClassifier(random_state=42, n_jobs=1)),
    ]
    return Pipeline(steps)


# ----------------------------------------------------------------------
# Nested cross‑validation
# ----------------------------------------------------------------------
def train_and_evaluate_nested_cv():
    logger = get_logger("04_train_model")

    # Load data
    features_df = load_features()
    subjects_df = load_eligible_subjects()

    # Align features with labels via subject_id
    X = features_df.set_index("subject_id")
    y = define_decline_label(subjects_df)
    y = pd.Series(y.values, index=subjects_df["subject_id"])
    # Ensure X and y have the same ordering
    X = X.loc[y.index]

    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    param_grid = {
        "clf__n_estimators": [50, 100, 200],
        "clf__max_depth": [5, 10, None],
    }

    best_score = -np.inf
    best_params = None

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y), start=1):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        pipeline = make_inner_pipeline()

        grid = GridSearchCV(
            estimator=pipeline,
            param_grid=param_grid,
            cv=inner_cv,
            scoring="roc_auc",
            n_jobs=2,
        )

        grid.fit(X_train, y_train)
        fold_score = grid.best_score_
        logger.info(f"Outer fold {fold_idx} best ROC‑AUC (inner CV): {fold_score:.4f}")

        if fold_score > best_score:
            best_score = fold_score
            best_params = grid.best_params_

    if best_params is None:
        logger.error("Grid search failed to produce any parameters.")
        sys.exit(2)

    logger.info(f"Selected hyper‑parameters after nested CV: {best_params}")

    # ------------------------------------------------------------------
    # Train final model on the full dataset with the selected hyper‑parameters
    # ------------------------------------------------------------------
    final_pipeline = make_inner_pipeline()
    final_pipeline.set_params(**best_params)
    final_pipeline.fit(X, y)

    # Persist the trained model
    ensure_dir(MODEL_PATH.parent)
    joblib.dump(final_pipeline, MODEL_PATH)
    logger.info(f"Final model written to {MODEL_PATH}")

    # Also write the chosen hyper‑parameters for downstream verification
    ensure_dir(TRAINING_PARAMS_PATH.parent)
    with TRAINING_PARAMS_PATH.open("w") as f:
        json.dump(best_params, f, indent=2)
    logger.info(f"Training parameters saved to {TRAINING_PARAMS_PATH}")

    return final_pipeline


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    train_and_evaluate_nested_cv()


if __name__ == "__main__":
    main()