"""
T023: Implement Nested CV training with collinearity handling, variance thresholding, and RFE.
"""
from __future__ import annotations

import json
import os
import sys
import time
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.feature_selection import VarianceThreshold, RFE
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import joblib

# Import shared utilities
from utils.logger import get_logger, log_operation
from utils.stats import check_collinearity, calculate_correlation_matrix, calculate_feature_variance
from utils.io import ensure_dir, load_csv, save_json

# Configuration
RANDOM_SEED = 42
DATA_PATH = Path("data/processed")
ELIGIBLE_FILE = DATA_PATH / "eligible_subjects.csv"
METRICS_FILE = DATA_PATH / "graph_metrics.csv"
MODEL_OUT = DATA_PATH / "model.pkl"
CV_RESULTS_OUT = DATA_PATH / "cv_results.json"
MODEL_PARAMS_OUT = DATA_PATH / "model_params.json"

logger = get_logger("train_model")


def load_features() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load graph metrics and labels.
    Returns: (X, y, feature_names)
    """
    if not ELIGIBLE_FILE.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_FILE}")
    if not METRICS_FILE.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {METRICS_FILE}")

    eligible_df = pd.read_csv(ELIGIBLE_FILE)
    eligible_ids = eligible_df['subject_id'].tolist()

    metrics_df = pd.read_csv(METRICS_FILE)
    
    # Ensure we only use eligible subjects
    metrics_df = metrics_df[metrics_df['subject_id'].isin(eligible_ids)]
    
    # Define decline label: drop >= 3 points
    # Assuming columns: subject_id, mmse_t1, mmse_t2, moca_t1, moca_t2 (or similar)
    # We need to handle potential missing columns gracefully
    mmse_cols = [c for c in metrics_df.columns if 'mmse' in c.lower()]
    moca_cols = [c for c in metrics_df.columns if 'moca' in c.lower()]
    
    if not mmse_cols and not moca_cols:
        raise ValueError("No MMSE or MOCA score columns found in graph_metrics.csv")

    # Prefer MMSE if available, else MOCA
    if mmse_cols and len(mmse_cols) >= 2:
        t1_col, t2_col = mmse_cols[0], mmse_cols[1]
    elif moca_cols and len(moca_cols) >= 2:
        t1_col, t2_col = moca_cols[0], moca_cols[1]
    else:
        raise ValueError("Need at least two timepoint scores (MMSE or MOCA) to calculate decline")

    # Calculate decline
    metrics_df['decline'] = metrics_df[t1_col] - metrics_df[t2_col]
    # Label: 1 if decline >= 3, else 0
    metrics_df['label'] = (metrics_df['decline'] >= 3).astype(int)

    # Filter for subjects with valid labels (non-NaN)
    valid_mask = metrics_df['label'].notna()
    metrics_df = metrics_df[valid_mask]

    # Feature columns: all numeric columns except subject_id and label/decline
    feature_cols = [c for c in metrics_df.columns if c not in ['subject_id', 'label', 'decline'] and pd.api.types.is_numeric_dtype(metrics_df[c])]
    
    if len(feature_cols) == 0:
        raise ValueError("No numeric feature columns found for training")

    X = metrics_df[feature_cols].values
    y = metrics_df['label'].values
    feature_names = feature_cols

    return X, y, feature_names


class CollinearityTransformer:
    """
    Custom transformer to handle collinearity within the pipeline.
    Excludes features with correlation > 0.95, keeping the higher-variance one.
    """
    def __init__(self, threshold=0.95):
        self.threshold = threshold
        self.keep_indices_ = None
        self.feature_names_ = None

    def fit(self, X, y=None):
        if X.shape[1] < 2:
            self.keep_indices_ = np.arange(X.shape[1])
            return self

        corr_matrix = np.corrcoef(X.T)
        np.fill_diagonal(corr_matrix, 0)  # Ignore self-correlation
        
        # Find pairs with high correlation
        high_corr_pairs = np.where(np.abs(corr_matrix) > self.threshold)
        
        # Keep track of indices to drop
        drop_indices = set()
        
        for i, j in zip(high_corr_pairs[0], high_corr_pairs[1]):
            if i >= j:  # Avoid duplicates and self
                continue
            
            # Calculate variance
            var_i = np.var(X[:, i])
            var_j = np.var(X[:, j])
            
            # Keep the one with higher variance
            if var_i >= var_j:
                drop_indices.add(j)
            else:
                drop_indices.add(i)
        
        self.keep_indices_ = np.array([i for i in range(X.shape[1]) if i not in drop_indices])
        return self

    def transform(self, X):
        if self.keep_indices_ is None:
            raise ValueError("Transformer not fitted yet.")
        return X[:, self.keep_indices_]


def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """
    Perform Nested Cross-Validation.
    Outer: Stratified K-Fold
    Inner: Grid Search with Feature Selection
    """
    logger.log("nested_cv_start", n_samples=X.shape[0], n_features=X.shape[1])

    # Grid Search Parameters
    param_grid = {
        'randomforestclassifier__n_estimators': [50, 100, 200],
        'randomforestclassifier__max_depth': [5, 10, None]
    }

    # Pipeline: Scaling -> Collinearity -> Variance Threshold -> RFE -> RF
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('collinearity', CollinearityTransformer(threshold=0.95)),
        ('variance', VarianceThreshold(threshold=0.01)),
        ('rfe', RFE(estimator=RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED), n_features_to_select=20)),
        ('randomforestclassifier', RandomForestClassifier(random_state=RANDOM_SEED))
    ])

    # Inner CV for Grid Search
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
    grid_search = GridSearchCV(
        pipe, 
        param_grid, 
        cv=inner_cv, 
        scoring='roc_auc', 
        n_jobs=2,
        return_train_score=False
    )

    # Outer CV
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    
    cv_results = []
    best_params_list = []
    auc_scores = []

    start_time = time.time()

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Fit Grid Search on training fold
        grid_search.fit(X_train, y_train)
        
        # Evaluate on test fold
        y_pred_proba = grid_search.predict_proba(X_test)[:, 1]
        fold_auc = roc_auc_score(y_test, y_pred_proba)
        auc_scores.append(fold_auc)
        
        cv_results.append({
            "fold": fold_idx + 1,
            "auc": float(fold_auc),
            "best_params": grid_search.best_params_,
            "n_test_samples": len(y_test)
        })
        best_params_list.append(grid_search.best_params_)

    elapsed_time = time.time() - start_time

    logger.log("nested_cv_complete", elapsed_seconds=elapsed_time, mean_auc=float(np.mean(auc_scores)))

    return {
        "cv_results": cv_results,
        "mean_auc": float(np.mean(auc_scores)),
        "std_auc": float(np.std(auc_scores)),
        "best_params": best_params_list[0] if best_params_list else {}, # Use first fold's best as representative
        "elapsed_time": elapsed_time
    }


def persist_model(X: np.ndarray, y: np.ndarray, feature_names: List[str], best_params: Dict[str, Any]) -> str:
    """
    Train a final model on the full dataset with the best parameters and save it.
    """
    # Reconstruct pipeline with best params
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('collinearity', CollinearityTransformer(threshold=0.95)),
        ('variance', VarianceThreshold(threshold=0.01)),
        ('rfe', RFE(estimator=RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED), n_features_to_select=20)),
        ('randomforestclassifier', RandomForestClassifier(**best_params, random_state=RANDOM_SEED))
    ])
    
    pipe.fit(X, y)
    
    model_artifact = {
        "pipeline": pipe,
        "feature_names": feature_names,
        "best_params": best_params
    }
    
    with open(MODEL_OUT, 'wb') as f:
        pickle.dump(model_artifact, f)
    
    logger.log("model_saved", path=str(MODEL_OUT))
    return str(MODEL_OUT)


def write_cv_results(results: Dict[str, Any]) -> None:
    """Write CV results to JSON."""
    with open(CV_RESULTS_OUT, 'w') as f:
        json.dump(results, f, indent=2)
    logger.log("cv_results_written", path=str(CV_RESULTS_OUT))


def write_model_params(params: Dict[str, Any]) -> None:
    """Write model parameters to JSON."""
    with open(MODEL_PARAMS_OUT, 'w') as f:
        json.dump(params, f, indent=2)
    logger.log("model_params_written", path=str(MODEL_PARAMS_OUT))


@log_operation("train_model_main")
def main() -> int:
    """Main entry point for T023."""
    try:
        logger.log("starting", operation="train_model")
        
        # Load data
        X, y, feature_names = load_features()
        logger.log("data_loaded", n_samples=X.shape[0], n_features=X.shape[1])

        # Train with Nested CV
        results = train_and_evaluate_nested_cv(X, y, feature_names)
        
        # Persist final model
        persist_model(X, y, feature_names, results['best_params'])
        
        # Write outputs
        write_cv_results(results)
        write_model_params(results['best_params'])
        
        logger.log("success", mean_auc=results['mean_auc'])
        return 0

    except Exception as e:
        logger.log("error", message=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())