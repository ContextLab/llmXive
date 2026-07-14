"""
Task T023: Train predictive model with nested cross-validation.

Implements:
- Decline label definition (MMSE/MOCA drop >= 3 points)
- Nested CV (Outer K-fold, Inner GridSearch)
- Feature selection pipeline inside inner loop:
  1. Collinearity check (drop corr > 0.95, keep higher variance)
  2. Variance thresholding (variance > 0.01)
  3. RFE (select <= 20 features)
- Random Forest training with grid search
- Outputs: model.pkl, cv_results.json, model_params.json
"""
from __future__ import annotations

import json
import sys
import time
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import warnings

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import (
    StratifiedKFold,
    GridSearchCV,
    cross_val_score,
    train_test_split,
)
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.base import TransformerMixin, BaseEstimator
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
import joblib

# Local imports
from config import apply_random_seed, get_config
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, save_json, save_pickle
from utils.stats import check_collinearity, calculate_feature_variance

# Suppress warnings for cleaner logs
warnings.filterwarnings("ignore")

# Constants
DECLINE_THRESHOLD = 3  # Points drop
MIN_VARIANCE = 0.01
MAX_FEATURES = 20
RANDOM_SEED = 42
OUTER_FOLDS = 5
INNER_FOLDS = 3

logger = get_logger("train_model")


class CollinearityTransformer(TransformerMixin, BaseEstimator):
    """
    Removes highly correlated features (Pearson > 0.95).
    Keeps the feature with higher variance when a pair is correlated.
    """

    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.mask_ = None
        self.correlation_matrix_ = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "CollinearityTransformer":
        n_features = X.shape[1]
        if n_features == 0:
            raise ValueError("No features to process")

        # Calculate correlation matrix
        corr_matrix = np.corrcoef(X, rowvar=False)
        self.correlation_matrix_ = corr_matrix

        # Create upper triangle mask to avoid double counting
        upper_tri = np.triu_indices(n_features, k=1)
        corr_upper = corr_matrix[upper_tri]

        # Identify pairs with correlation > threshold
        high_corr_pairs = np.where(np.abs(corr_upper) > self.threshold)[0]

        # Initialize mask to keep all features (True = keep)
        self.mask_ = np.ones(n_features, dtype=bool)

        if len(high_corr_pairs) > 0:
            # Calculate variances for all features
            variances = np.var(X, axis=0)

            for idx in high_corr_pairs:
                i, j = upper_tri[0][idx], upper_tri[1][idx]
                
                # Keep the one with higher variance
                if variances[i] >= variances[j]:
                    self.mask_[j] = False
                else:
                    self.mask_[i] = False

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self.mask_ is None:
            raise RuntimeError("Transformer not fitted. Call fit() first.")
        return X[:, self.mask_]

    def get_feature_names_out(self, input_features=None):
        if self.mask_ is None:
            raise RuntimeError("Transformer not fitted.")
        if input_features is None:
            input_features = [f"feature_{i}" for i in range(len(self.mask_))]
        return np.array(input_features)[self.mask_]


def load_eligible_subjects() -> List[str]:
    """Load list of eligible subject IDs from CSV."""
    path = Path("data/processed/eligible_subjects.csv")
    if not path.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {path}")
    
    df = pd.read_csv(path)
    subjects = df["subject_id"].tolist()
    logger.log("load_eligible_subjects", count=len(subjects), status="success")
    return subjects


def load_features(subjects: List[str]) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    Load graph metrics for eligible subjects.
    Returns: (features_array, labels_series)
    """
    metrics_path = Path("data/processed/graph_metrics.csv")
    if not metrics_path.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {metrics_path}")
    
    df = pd.read_csv(metrics_path)
    
    # Filter for eligible subjects
    df = df[df["subject_id"].isin(subjects)]
    
    if len(df) == 0:
        raise ValueError("No eligible subjects found in graph metrics file.")
    
    # Define decline label
    # Assuming columns: 'mmse_t1', 'mmse_t2' or 'moca_t1', 'moca_t2'
    # We need to detect which columns exist
    t1_cols = [c for c in df.columns if ("mmse" in c.lower() or "moca" in c.lower()) and ("t1" in c.lower() or "baseline" in c.lower())]
    t2_cols = [c for c in df.columns if ("mmse" in c.lower() or "moca" in c.lower()) and ("t2" in c.lower() or "followup" in c.lower())]
    
    if not t1_cols or not t2_cols:
        # Fallback: try to find any score columns and assume order
        score_cols = [c for c in df.columns if ("mmse" in c.lower() or "moca" in c.lower())]
        if len(score_cols) >= 2:
            t1_cols = [score_cols[0]]
            t2_cols = [score_cols[1]]
        else:
            raise ValueError("Could not find baseline and follow-up cognitive scores.")
    
    t1_col = t1_cols[0]
    t2_col = t2_cols[0]
    
    # Calculate decline
    # Drop >= 3 points means: t1 - t2 >= 3
    df["score_drop"] = df[t1_col].astype(float) - df[t2_col].astype(float)
    df["decline_label"] = (df["score_drop"] >= DECLINE_THRESHOLD).astype(int)
    
    # Prepare features (drop subject_id and label columns)
    feature_cols = [c for c in df.columns if c not in ["subject_id", t1_col, t2_col, "score_drop", "decline_label"]]
    
    if not feature_cols:
        raise ValueError("No feature columns found in graph metrics.")
    
    X = df[feature_cols].values.astype(np.float32)
    y = df["decline_label"].values
    
    logger.log(
        "load_features",
        n_subjects=len(df),
        n_features=X.shape[1],
        n_positive=int(y.sum()),
        n_negative=len(y) - int(y.sum()),
        status="success"
    )
    
    return X, y


def define_decline_label(y_scores_drop: np.ndarray) -> np.ndarray:
    """Define binary label: 1 if drop >= 3, else 0."""
    return (y_scores_drop >= DECLINE_THRESHOLD).astype(int)


def train_and_evaluate_nested_cv(
    X: np.ndarray,
    y: np.ndarray
) -> Tuple[Any, Dict[str, Any], Dict[str, Any]]:
    """
    Perform nested cross-validation.
    Outer: Stratified K-Fold for evaluation.
    Inner: GridSearchCV for hyperparameter tuning + feature selection.
    
    Returns: (best_model, cv_results_dict, best_params_dict)
    """
    logger.log("nested_cv_start", n_samples=X.shape[0], n_features=X.shape[1])
    
    # Hyperparameter grid
    param_grid = {
        "randomforestclassifier__n_estimators": [50, 100, 200],
        "randomforestclassifier__max_depth": [5, 10, None],
    }
    
    # Outer CV
    outer_cv = StratifiedKFold(n_splits=OUTER_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    
    # Inner CV
    inner_cv = StratifiedKFold(n_splits=INNER_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    
    # Pipeline: Collinearity -> Variance Threshold -> RFE -> RF
    pipeline = Pipeline([
        ("collinearity", CollinearityTransformer(threshold=0.95)),
        ("variance", VarianceThreshold(threshold=MIN_VARIANCE)),
        ("rfe", RFE(estimator=RandomForestClassifier(random_state=RANDOM_SEED, n_estimators=10), n_features_to_select=MAX_FEATURES)),
        ("randomforestclassifier", RandomForestClassifier(random_state=RANDOM_SEED)),
    ])
    
    # Store results
    outer_scores = []
    all_cv_results = []
    best_params_list = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Grid Search inside inner loop
        grid_search = GridSearchCV(
            pipeline,
            param_grid,
            cv=inner_cv,
            scoring="roc_auc",
            n_jobs=2,
            refit=True,
            return_train_score=True,
            verbose=0
        )
        
        try:
            grid_search.fit(X_train, y_train)
            
            # Evaluate on outer test set
            y_pred_proba = grid_search.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, y_pred_proba)
            outer_scores.append(auc)
            
            # Store details
            all_cv_results.append({
                "fold": fold_idx,
                "test_auc": float(auc),
                "best_params": grid_search.best_params_,
                "cv_results": grid_search.cv_results_
            })
            best_params_list.append(grid_search.best_params_)
            
            logger.log(
                "fold_complete",
                fold=fold_idx,
                test_auc=float(auc),
                best_params=grid_search.best_params_
            )
            
        except Exception as e:
            logger.log("fold_failed", fold=fold_idx, error=str(e))
            # Skip this fold if it fails (e.g., not enough samples for RFE)
            continue
    
    if not outer_scores:
        raise RuntimeError("No folds completed successfully.")
    
    # Refit on full data with best average params
    # Use the most common best_params or average
    # For simplicity, we'll use the params from the first successful fold
    # In a production setting, you might aggregate better
    final_params = best_params_list[0]
    
    final_pipeline = Pipeline([
        ("collinearity", CollinearityTransformer(threshold=0.95)),
        ("variance", VarianceThreshold(threshold=MIN_VARIANCE)),
        ("rfe", RFE(estimator=RandomForestClassifier(random_state=RANDOM_SEED, n_estimators=10), n_features_to_select=MAX_FEATURES)),
        ("randomforestclassifier", RandomForestClassifier(random_state=RANDOM_SEED)),
    ])
    
    final_pipeline.set_params(**final_params)
    final_pipeline.fit(X, y)
    
    results_dict = {
        "outer_folds": outer_scores,
        "mean_auc": float(np.mean(outer_scores)),
        "std_auc": float(np.std(outer_scores)),
        "fold_details": all_cv_results
    }
    
    params_dict = {
        "best_params": final_params,
        "n_samples": X.shape[0],
        "n_features_initial": X.shape[1],
        "outer_folds": OUTER_FOLDS,
        "inner_folds": INNER_FOLDS
    }
    
    logger.log(
        "nested_cv_complete",
        mean_auc=float(np.mean(outer_scores)),
        std_auc=float(np.std(outer_scores)),
        status="success"
    )
    
    return final_pipeline, results_dict, params_dict


def persist_model(model: Any, path: str) -> None:
    """Save model to disk."""
    ensure_dir(path)
    joblib.dump(model, path)
    logger.log("persist_model", path=path, status="success")


def write_performance_report(results: Dict[str, Any], params: Dict[str, Any], path: str) -> None:
    """Write CV results and params to JSON."""
    report = {
        "cv_results": results,
        "model_params": params,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    save_json(report, path)
    logger.log("write_performance_report", path=path, status="success")


def main() -> int:
    """Main entry point."""
    start_time = time.time()
    apply_random_seed(RANDOM_SEED)
    
    try:
        # 1. Load data
        subjects = load_eligible_subjects()
        X, y = load_features(subjects)
        
        # 2. Train model
        model, cv_results, model_params = train_and_evaluate_nested_cv(X, y)
        
        # 3. Persist outputs
        model_path = "data/processed/model.pkl"
        cv_results_path = "data/processed/cv_results.json"
        params_path = "data/processed/model_params.json"
        
        persist_model(model, model_path)
        write_performance_report(cv_results, model_params, cv_results_path)
        write_performance_report({}, model_params, params_path) # Simplified for params-only file
        
        elapsed = time.time() - start_time
        logger.log("main_complete", elapsed_seconds=elapsed, status="success")
        
        return 0
        
    except Exception as e:
        logger.log("main_failed", error=str(e), status="failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())