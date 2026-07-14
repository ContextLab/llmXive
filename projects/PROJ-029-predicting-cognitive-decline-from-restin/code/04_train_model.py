"""Train a Random Forest model with nested cross‑validation.\n

This script reads the eligible subjects list and the pre‑computed graph metrics,\n      constructs a decline label (drop ≥ 3 points on MMSE/MOCA), performs a collinearity\n      filter, variance thresholding, and Recursive Feature Elimination (RFE) before\n      training a Random Forest inside a nested CV framework.\n      

Outputs:\n      - ``data/processed/model.pkl`` – the best estimator fitted on the full data.\n      - ``data/processed/performance_report.json`` – mean ROC‑AUC, accuracy and F1‑score.\n      """

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
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold

# Local utilities ------------------------------------------------------------
from utils.logger import get_logger, log_operation
from utils.io import load_csv, save_pickle, save_json

# -------------------------------------------------------------------------
# Configuration constants
# -------------------------------------------------------------------------
DATA_DIR = Path("data") / "processed"
ELIGIBLE_SUBJECTS_PATH = DATA_DIR / "eligible_subjects.csv"
GRAPH_METRICS_PATH = DATA_DIR / "graph_metrics.csv"
MODEL_PATH = DATA_DIR / "model.pkl"
PERFORMANCE_REPORT_PATH = DATA_DIR / "performance_report.json"

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def load_eligible_subjects() -> pd.DataFrame:
    """Load the CSV produced by ``01_download_and_filter``."""
    logger = get_logger("load_eligible")
    logger.info("Loading eligible subjects from %s", ELIGIBLE_SUBJECTS_PATH)
    df = pd.read_csv(ELIGIBLE_SUBJECTS_PATH)
    return df


def load_features() -> pd.DataFrame:
    """Load the graph‑metric feature matrix."""
    logger = get_logger("load_features")
    logger.info("Loading graph metrics from %s", GRAPH_METRICS_PATH)
    df = pd.read_csv(GRAPH_METRICS_PATH)
    return df


def define_decline_label(df: pd.DataFrame, score_col_t1: str = "mmse_t1", score_col_t2: str = "mmse_t2") -> np.ndarray:
    """
    Create a binary label: 1 if the subject’s score dropped by ≥ 3 points,
    otherwise 0.
    """
    logger = get_logger("label_definition")
    if not {score_col_t1, score_col_t2}.issubset(df.columns):
        logger.error("Score columns %s and %s not found in eligible subjects dataframe.", score_col_t1, score_col_t2)
        raise KeyError("Required score columns missing.")
    decline = (df[score_col_t1] - df[score_col_t2]) >= 3
    logger.info("Defined decline label for %d subjects (positive: %d).", len(df), decline.sum())
    return decline.astype(int).values


class CollinearityTransformer(BaseEstimator, TransformerMixin):
    """
    Drop one feature from each pair with Pearson correlation > ``threshold``.
    The feature with the lower variance is removed.
    """

    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.features_to_keep_: List[str] = []

    def fit(self, X: pd.DataFrame, y: Any = None):
        # Compute absolute correlation matrix
        corr = X.corr().abs()
        # Upper triangle mask
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        # Identify column pairs above the threshold
        to_drop = set()
        for col in upper.columns:
            high_corr = upper[col][upper[col] > self.threshold].index.tolist()
            for partner in high_corr:
                # Keep the column with higher variance
                var_col = X[col].var()
                var_partner = X[partner].var()
                drop_col = col if var_col < var_partner else partner
                to_drop.add(drop_col)
        self.features_to_keep_ = [c for c in X.columns if c not in to_drop]
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        return X[self.features_to_keep_]


def make_inner_pipeline() -> Tuple[Any, Dict[str, List[Any]]]:
    """
    Build the inner pipeline and the associated hyper‑parameter grid.

    Returns:
        pipeline: sklearn Pipeline object.
        param_grid: dict mapping parameter names to lists of values.
    """
    pipeline = joblib.pipeline.Pipeline(
        steps=[
            ("collinearity", CollinearityTransformer()),
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


def train_and_evaluate_nested_cv(X: pd.DataFrame, y: np.ndarray) -> Tuple[RandomForestClassifier, Dict[str, Any]]:
    """
    Perform 5‑fold outer CV with an inner grid‑search CV.

    Returns:
        best_estimator: RandomForestClassifier trained on the full dataset
                        using the best hyper‑parameters found.
        report: Dictionary containing mean ROC‑AUC, accuracy and F1‑score,
                plus the hyper‑parameters selected in the outer fold that
                achieved the highest mean score.
    """
    logger = get_logger("nested_cv")
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    outer_metrics = {"roc_auc": [], "accuracy": [], "f1": []}
    best_params_across_folds = []

    pipeline, param_grid = make_inner_pipeline()

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y), start=1):
        logger.info("Outer CV fold %d / 5", fold_idx)
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        inner_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        grid = GridSearchCV(
            estimator=pipeline,
            param_grid=param_grid,
            cv=inner_cv,
            scoring="roc_auc",
            n_jobs=2,
        )

        grid.fit(X_train, y_train)
        best_params_across_folds.append(grid.best_params_)

        # Predict on the outer‑test split
        y_proba = grid.predict_proba(X_test)[:, 1]
        y_pred = (y_proba >= 0.5).astype(int)

        roc = roc_auc_score(y_test, y_proba)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        logger.info(
            "Fold %d results – ROC‑AUC: %.4f, Acc: %.4f, F1: %.4f",
            fold_idx,
            roc,
            acc,
            f1,
        )

        outer_metrics["roc_auc"].append(roc)
        outer_metrics["accuracy"].append(acc)
        outer_metrics["f1"].append(f1)

    # Aggregate results
    mean_report = {
        "mean_roc_auc": float(np.mean(outer_metrics["roc_auc"])),
        "mean_accuracy": float(np.mean(outer_metrics["accuracy"])),
        "mean_f1": float(np.mean(outer_metrics["f1"])),
    }
    # Choose the most frequently selected hyper‑parameters
    from collections import Counter

    most_common_params = Counter(tuple(sorted(p.items())) for p in best_params_across_folds).most_common(1)[0][0]
    best_params = dict(most_common_params)
    mean_report["selected_hyperparameters"] = best_params

    logger.info("Nested CV completed. Report: %s", mean_report)

    # Re‑fit on the full dataset using the selected hyper‑parameters
    final_pipeline = joblib.pipeline.Pipeline(
        steps=[
            ("collinearity", CollinearityTransformer()),
            ("variance", VarianceThreshold(threshold=0.01)),
            ("rfe", RFE(estimator=RandomForestClassifier(random_state=42), n_features_to_select=20)),
            ("clf", RandomForestClassifier(random_state=42, **best_params)),
        ]
    )
    final_pipeline.fit(X, y)
    # The final estimator is the RandomForest inside the pipeline
    final_model = final_pipeline.named_steps["clf"]
    return final_model, mean_report


def persist_model(model: RandomForestClassifier) -> None:
    """Serialize the trained RandomForest to disk."""
    logger = get_logger("persist_model")
    logger.info("Persisting model to %s", MODEL_PATH)
    save_pickle(model, MODEL_PATH)


def write_performance_report(report: Dict[str, Any]) -> None:
    """Write the performance metrics to a JSON file."""
    logger = get_logger("performance_report")
    logger.info("Writing performance report to %s", PERFORMANCE_REPORT_PATH)
    save_json(report, PERFORMANCE_REPORT_PATH)


@log_operation("train_model")
def main() -> None:
    """Entry point for the training script."""
    logger = get_logger("train_model")
    try:
        # ------------------------------------------------------------------
        # Load data
        # ------------------------------------------------------------------
        subjects_df = load_eligible_subjects()
        features_df = load_features()

        # Ensure we have a common identifier column named ``subject_id``
        if "subject_id" not in subjects_df.columns or "subject_id" not in features_df.columns:
            logger.error("Both data frames must contain a 'subject_id' column.")
            sys.exit(1)

        # Merge on subject_id
        merged = pd.merge(subjects_df, features_df, on="subject_id", how="inner")
        if merged.empty:
            logger.error("No overlapping subjects between eligibility list and graph metrics.")
            sys.exit(1)

        # ------------------------------------------------------------------
        # Create label
        # ------------------------------------------------------------------
        y = define_decline_label(merged)

        # Drop non‑feature columns before modelling
        X = merged.drop(columns=["subject_id", "mmse_t1", "mmse_t2"], errors="ignore")

        # ------------------------------------------------------------------
        # Train / evaluate
        # ------------------------------------------------------------------
        model, report = train_and_evaluate_nested_cv(X, y)

        # ------------------------------------------------------------------
        # Persist artefacts
        # ------------------------------------------------------------------
        persist_model(model)
        write_performance_report(report)

        logger.info("Training pipeline completed successfully.")
    except Exception as exc:
        logger.error("Training failed: %s", exc)
        raise


if __name__ == "__main__":
    main()