"""
code/04_train_model.py
Train a Random Forest classifier with nested cross-validation to predict cognitive decline.

Decline label: drop >= 3 points in MMSE/MOCA between timepoints.
Nested CV: K-fold outer, grid-search inner.
Grid Search: n_estimators in {50, 100, 200}, max_depth in {5, 10, None}.
Inner Loop: Collinearity check (corr > 0.95), Variance Threshold (> 0.01), RFE (<= 20 features).
Outputs: data/processed/model.pkl, data/processed/cv_results.json, data/processed/model_params.json.
"""
from __future__ import annotations

import json
import os
import sys
import time
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import roc_auc_score
from joblib import Parallel, delayed
import psutil

# Project-relative imports
# Note: We assume this script is run from the project root or code directory
# Adjust sys.path if necessary, but standard practice in this repo is to run from root
if "code" not in sys.path:
    sys.path.insert(0, "code")

from utils.logger import get_logger, log_operation
from utils.stats import check_collinearity, calculate_correlation_matrix, calculate_feature_variance
from utils.io import save_pickle, save_json, ensure_dir
from config import get_config

logger = get_logger("train_model")

# --- Constants ---
DECLINE_THRESHOLD = 3  # Points drop to define decline
MIN_VARIANCE = 0.01
MAX_FEATURES = 20
CORRELATION_THRESHOLD = 0.95
RANDOM_SEED = 42
N_JOBS = 2  # For joblib parallelization within constraints

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
MODEL_PATH = DATA_PROCESSED / "model.pkl"
CV_RESULTS_PATH = DATA_PROCESSED / "cv_results.json"
MODEL_PARAMS_PATH = DATA_PROCESSED / "model_params.json"
GRAPH_METRICS_PATH = DATA_PROCESSED / "graph_metrics.csv"
ELIGIBLE_SUBJECTS_PATH = DATA_PROCESSED / "eligible_subjects.csv"

# Grid Search Parameters
PARAM_GRID = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, None]
}

class CollinearityTransformer(BaseEstimator, TransformerMixin):
    """
    Removes features with pairwise correlation > threshold, keeping the one with higher variance.
    Implements the logic required inside the inner CV loop.
    """
    def __init__(self, threshold: float = CORRELATION_THRESHOLD):
        self.threshold = threshold
        self.keep_indices_ = None
        self.correlation_matrix_ = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "CollinearityTransformer":
        if X.shape[1] == 0:
            self.keep_indices_ = np.array([])
            return self

        # Calculate correlation matrix
        corr_matrix = np.corrcoef(X, rowvar=False)
        self.correlation_matrix_ = corr_matrix

        # Identify high correlation pairs
        n_features = X.shape[1]
        keep = np.ones(n_features, dtype=bool)
        
        # Upper triangle only (excluding diagonal)
        upper_tri = np.triu_indices(n_features, k=1)
        
        for i, j in zip(upper_tri[0], upper_tri[1]):
            if abs(corr_matrix[i, j]) > self.threshold:
                # Keep the one with higher variance
                var_i = np.var(X[:, i])
                var_j = np.var(X[:, j])
                if var_i < var_j:
                    keep[i] = False
                else:
                    keep[j] = False
        
        self.keep_indices_ = np.where(keep)[0]
        logger.log("collinearity_filter", 
                   operation="collinearity_filter", 
                   original_features=n_features, 
                   kept_features=len(self.keep_indices_),
                   threshold=self.threshold)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if len(self.keep_indices_) == 0:
            return np.zeros((X.shape[0], 0))
        return X[:, self.keep_indices_]

def load_features() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Loads graph metrics and labels.
    Returns: (X, y, feature_names)
    """
    if not GRAPH_METRICS_PATH.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {GRAPH_METRICS_PATH}")
    
    df = pd.read_csv(GRAPH_METRICS_PATH)
    
    # Ensure 'data' column exists as per contract, or use the first numeric column if 'data' is missing
    # Based on execution failures, consumers expect a 'data' column or specific structure.
    # Assuming the CSV has subject_id and metric columns. We need to identify the target.
    # The task says "Define decline label". We need to calculate it from the raw scores if available,
    # or assume it's pre-computed.
    # Looking at T017, it outputs eligible_subjects.csv. T019 outputs graph_metrics.csv.
    # We need to join these to get the decline label.
    
    eligible_df = pd.read_csv(ELIGIBLE_SUBJECTS_PATH)
    
    # Merge to get labels
    # Assuming eligible_subjects.csv has: subject_id, mmse_t1, mmse_t2, moca_t1, moca_t2, decline_label
    # If decline_label is not present, calculate it.
    if 'decline_label' not in eligible_df.columns:
        # Calculate decline based on MMSE if available, else MOCA
        if 'mmse_t1' in eligible_df.columns and 'mmse_t2' in eligible_df.columns:
            eligible_df['score_diff'] = eligible_df['mmse_t1'] - eligible_df['mmse_t2']
        elif 'moca_t1' in eligible_df.columns and 'moca_t2' in eligible_df.columns:
            eligible_df['score_diff'] = eligible_df['moca_t1'] - eligible_df['moca_t2']
        else:
            raise ValueError("No cognitive score columns found to calculate decline label.")
        
        eligible_df['decline_label'] = (eligible_df['score_diff'] >= DECLINE_THRESHOLD).astype(int)

    merged = pd.merge(df, eligible_df[['subject_id', 'decline_label']], on='subject_id', how='inner')
    
    if merged.empty:
        raise ValueError("No overlapping subjects between graph metrics and eligible subjects.")

    feature_cols = [c for c in merged.columns if c not in ['subject_id', 'decline_label']]
    
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found in graph_metrics.csv.")

    X = merged[feature_cols].values
    y = merged['decline_label'].values
    
    # Handle NaNs
    if np.any(np.isnan(X)):
        logger.log("data_cleaning", operation="fill_nan", strategy="median")
        X = np.nan_to_num(X, nan=np.nanmedian(X))
        
    return X, y, feature_cols

def train_single_fold(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trains a single fold with nested feature selection and model training.
    Returns metrics and results.
    """
    # 1. Variance Thresholding
    vt = VarianceThreshold(threshold=MIN_VARIANCE)
    X_train_vt = vt.fit_transform(X_train)
    X_test_vt = vt.transform(X_test)
    
    # 2. Collinearity Check (inside inner loop, but here we simulate the inner loop logic for a single fold)
    # Actually, in nested CV, feature selection happens in the inner loop (on training fold).
    # For this function, we assume it's called from the inner loop or we simulate the inner loop here.
    # To strictly follow "Inside the inner CV loop", this function should be the inner estimator.
    # But for simplicity in this script structure, we'll do the full inner logic here if called directly,
    # or assume the GridSearchCV handles the pipeline.
    
    # We need a pipeline: VarianceThreshold -> Collinearity -> RFE -> RandomForest
    # However, RFE requires an estimator.
    
    # Let's construct the pipeline
    collinear = CollinearityTransformer(threshold=CORRELATION_THRESHOLD)
    # RFE needs an estimator. We use a default RF for selection
    rf_base = RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED, max_depth=5)
    rfe = RFE(estimator=rf_base, n_features_to_select=min(MAX_FEATURES, X_train_vt.shape[1]))
    
    # Note: RFE might fail if features < n_features_to_select. We handle that in the wrapper.
    current_max_features = min(MAX_FEATURES, X_train_vt.shape[1])
    if current_max_features <= 0:
        return {"roc_auc": 0.0, "error": "No features left after filtering"}
    
    rfe.n_features_to_select = current_max_features
    
    rf_final = RandomForestClassifier(**params, random_state=RANDOM_SEED)
    
    # Pipeline: Variance -> Collinearity -> RFE -> RF
    # Note: sklearn pipeline requires all steps to be transformers except the last.
    # CollinearityTransformer is a transformer. VarianceThreshold is a transformer. RFE is a transformer.
    
    pipeline = Pipeline([
        ('variance', vt),
        ('collinearity', collinear),
        ('rfe', rfe),
        ('rf', rf_final)
    ])
    
    # Fit
    try:
        pipeline.fit(X_train, y_train)
        y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
        
        # Handle edge case where only one class exists in test set (AUC undefined)
        if len(np.unique(y_test)) < 2:
            auc = 0.5 # Default or handle as error? Spec says ROC-AUC > 0.5, so 0.5 is baseline.
        else:
            auc = roc_auc_score(y_test, y_pred_proba)
            
        return {"roc_auc": float(auc), "status": "success", "n_features_selected": len(pipeline.named_steps['rfe'].support_)}
    except Exception as e:
        logger.log("fold_error", operation="train_fold", error=str(e))
        return {"roc_auc": 0.0, "error": str(e)}

def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray) -> Tuple[Any, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Runs the full nested cross-validation.
    Outer: Stratified K-Fold
    Inner: Grid Search with feature selection inside the pipeline.
    """
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    
    cv_results = []
    all_aucs = []
    best_params_count = {}
    
    # We need to wrap the grid search inside the pipeline to ensure feature selection happens per fold
    # The pipeline defined in train_single_fold is the base. We need to inject the grid search over the RF params.
    # However, GridSearchCV wraps the whole estimator.
    # So the pipeline passed to GridSearchCV will be:
    # Pipeline([ ..., ('rf', RandomForestClassifier()) ])
    # And we search over 'rf__n_estimators', 'rf__max_depth'.
    
    # Re-defining the pipeline structure for GridSearchCV
    # We cannot easily put RFE and Collinearity in a way that GridSearchCV optimizes RF params 
    # without them being re-fitted every time. This is the correct behavior for nested CV.
    
    # Base pipeline for the inner loop
    base_pipeline = Pipeline([
        ('variance', VarianceThreshold(threshold=MIN_VARIANCE)),
        ('collinearity', CollinearityTransformer(threshold=CORRELATION_THRESHOLD)),
        ('rfe', RFE(estimator=RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED), 
                    n_features_to_select=min(MAX_FEATURES, X.shape[1]))),
        ('rf', RandomForestClassifier(random_state=RANDOM_SEED))
    ])
    
    # Adjust RFE features dynamically? RFE in pipeline is fixed at init. 
    # We might need a custom transformer or just set it to a safe max and let RFE handle it?
    # RFE will select n_features_to_select. If we set it to MAX_FEATURES, and features are fewer, it might error.
    # We'll set it to MAX_FEATURES and handle the error in the fold loop.
    base_pipeline.named_steps['rfe'].n_features_to_select = MAX_FEATURES
    
    grid_search = GridSearchCV(
        estimator=base_pipeline,
        param_grid=PARAM_GRID,
        cv=3, # Inner CV folds
        scoring='roc_auc',
        n_jobs=N_JOBS,
        refit=True
    )
    
    outer_scores = []
    fold_details = []
    
    logger.log("start_nested_cv", operation="nested_cv", n_splits=5, inner_cv=3)
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_tr, X_te = X[train_idx], X[test_idx]
        y_tr, y_te = y[train_idx], y[test_idx]
        
        # Dynamic adjustment for RFE if features are too few
        current_max = min(MAX_FEATURES, X_tr.shape[1])
        if current_max <= 0:
            fold_details.append({"fold": fold_idx, "error": "Insufficient features"})
            continue
        
        # We need to re-instantiate the pipeline for each fold to reset RFE state?
        # Actually, GridSearchCV fits from scratch. But RFE's n_features_to_select is set at init.
        # We can't change it easily inside the loop without re-creating the pipeline object.
        # Let's create a fresh pipeline for each fold to ensure RFE is set correctly.
        
        fresh_pipeline = Pipeline([
            ('variance', VarianceThreshold(threshold=MIN_VARIANCE)),
            ('collinearity', CollinearityTransformer(threshold=CORRELATION_THRESHOLD)),
            ('rfe', RFE(estimator=RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED), 
                        n_features_to_select=current_max)),
            ('rf', RandomForestClassifier(random_state=RANDOM_SEED))
        ])
        
        fresh_grid = GridSearchCV(
            estimator=fresh_pipeline,
            param_grid=PARAM_GRID,
            cv=3,
            scoring='roc_auc',
            n_jobs=N_JOBS,
            refit=True
        )
        
        try:
            fresh_grid.fit(X_tr, y_tr)
            best_model = fresh_grid.best_estimator_
            y_pred_proba = best_model.predict_proba(X_te)[:, 1]
            
            if len(np.unique(y_te)) < 2:
                auc = 0.5
            else:
                auc = roc_auc_score(y_te, y_pred_proba)
            
            outer_scores.append(auc)
            
            fold_details.append({
                "fold": fold_idx,
                "auc": float(auc),
                "best_params": fresh_grid.best_params_,
                "cv_mean_score": float(fresh_grid.best_score_),
                "status": "success"
            })
            
        except Exception as e:
            logger.log("fold_error", operation="fold_" + str(fold_idx), error=str(e))
            fold_details.append({"fold": fold_idx, "error": str(e)})
    
    mean_auc = np.mean(outer_scores) if outer_scores else 0.0
    
    # Final model training on full data with best params found
    # We re-run the grid search on the full data to get the final model
    final_pipeline = Pipeline([
        ('variance', VarianceThreshold(threshold=MIN_VARIANCE)),
        ('collinearity', CollinearityTransformer(threshold=CORRELATION_THRESHOLD)),
        ('rfe', RFE(estimator=RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED), 
                    n_features_to_select=min(MAX_FEATURES, X.shape[1]))),
        ('rf', RandomForestClassifier(random_state=RANDOM_SEED))
    ])
    
    final_grid = GridSearchCV(
        estimator=final_pipeline,
        param_grid=PARAM_GRID,
        cv=3,
        scoring='roc_auc',
        n_jobs=N_JOBS,
        refit=True
    )
    final_grid.fit(X, y)
    best_model = final_grid.best_estimator_
    
    return best_model, {
        "mean_outer_auc": float(mean_auc),
        "std_outer_auc": float(np.std(outer_scores)) if outer_scores else 0.0,
        "outer_scores": [float(x) for x in outer_scores],
        "fold_details": fold_details
    }, final_grid.cv_results_

def persist_model(model: Any, path: Path) -> None:
    """Saves the trained model to disk."""
    ensure_dir(path)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.log("model_saved", operation="persist_model", path=str(path))

def write_cv_results(results: Dict[str, Any], path: Path) -> None:
    """Writes CV results to JSON."""
    ensure_dir(path)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.log("cv_results_saved", operation="write_cv_results", path=str(path))

def write_model_params(params: Dict[str, Any], path: Path) -> None:
    """Writes model parameters to JSON."""
    ensure_dir(path)
    with open(path, 'w') as f:
        json.dump(params, f, indent=2)
    logger.log("model_params_saved", operation="write_model_params", path=str(path))

@log_operation
def main() -> int:
    """Main entry point for training."""
    start_time = time.time()
    logger.log("train_model_main", operation="start")
    
    try:
        # 1. Load Data
        X, y, feature_names = load_features()
        logger.log("data_loaded", operation="load_features", n_samples=X.shape[0], n_features=X.shape[1])
        
        if len(np.unique(y)) < 2:
            logger.log("error", operation="check_labels", error="Only one class found in labels.")
            return 1
        
        # 2. Train Model
        model, cv_summary, cv_full_results = train_and_evaluate_nested_cv(X, y)
        
        # 3. Persist Artifacts
        persist_model(model, MODEL_PATH)
        write_cv_results(cv_summary, CV_RESULTS_PATH)
        
        # Extract best params for the params file
        best_params = model.named_steps['rf'].get_params()
        # We also want the pipeline params
        full_params = {
            "best_pipeline_params": model.named_steps['rf'].get_params(),
            "grid_search_params": PARAM_GRID,
            "feature_selection": {
                "variance_threshold": MIN_VARIANCE,
                "collinearity_threshold": CORRELATION_THRESHOLD,
                "rfe_max_features": MAX_FEATURES
            },
            "decline_threshold": DECLINE_THRESHOLD,
            "random_seed": RANDOM_SEED
        }
        write_model_params(full_params, MODEL_PARAMS_PATH)
        
        elapsed = time.time() - start_time
        logger.log("train_model_complete", operation="end", elapsed_seconds=elapsed, mean_auc=cv_summary["mean_outer_auc"])
        
        print(f"Training complete. Mean AUC: {cv_summary['mean_outer_auc']:.4f}")
        print(f"Model saved to {MODEL_PATH}")
        print(f"CV Results saved to {CV_RESULTS_PATH}")
        print(f"Model Params saved to {MODEL_PARAMS_PATH}")
        
        return 0
        
    except Exception as e:
        logger.log("error", operation="main", error=str(e))
        print(f"Error during training: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())