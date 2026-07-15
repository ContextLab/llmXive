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
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score
from scipy.stats import pearsonr
import joblib

# Import from project utilities
from utils.logger import get_logger, log_operation
from utils.stats import check_collinearity, calculate_correlation_matrix, calculate_feature_variance, filter_low_variance_features
from utils.io import load_csv, save_json

logger = get_logger("train_model")

# Constants
DECREASE_THRESHOLD = 3  # Decline defined as drop >= 3 points
RANDOM_SEED = 42
MAX_FEATURES = 20
CORR_THRESHOLD = 0.95
VAR_THRESHOLD = 0.01
N_ESTIMATORS_GRID = [50, 100, 200]
MAX_DEPTH_GRID = [5, 10, None]
N_JOBS = 2

@log_operation
def load_features(subject_ids: List[str], metrics_file: str = "data/processed/graph_metrics.csv") -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load graph metrics and labels (decline) from the processed data.
    Returns: (X, y, feature_names)
    """
    logger.log("load_features_start", file=metrics_file, n_subjects=len(subject_ids))
    
    # Load the graph metrics
    df = pd.read_csv(metrics_file)
    
    # Ensure subject_id column exists and matches input
    if 'subject_id' not in df.columns:
        raise ValueError(f"CSV must contain 'subject_id' column. Found: {df.columns.tolist()}")
    
    # Filter to only requested subjects
    df = df[df['subject_id'].isin(subject_ids)].copy()
    
    if len(df) != len(subject_ids):
        missing = set(subject_ids) - set(df['subject_id'].tolist())
        logger.log("load_features_warning", missing_subjects=list(missing))
    
    # Identify feature columns (exclude subject_id and label columns if present)
    exclude_cols = ['subject_id', 'decline_label', 'mmse_baseline', 'mmse_followup', 'moca_baseline', 'moca_followup']
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in graph metrics CSV.")
    
    X = df[feature_cols].values.astype(np.float64)
    
    # Calculate labels: decline >= 3 points
    # We need to calculate this from the raw scores if not already present
    # Assuming the CSV has baseline and followup scores for MMSE or MOCa
    y = np.zeros(len(df), dtype=int)
    
    # Try MMSE first
    if 'mmse_baseline' in df.columns and 'mmse_followup' in df.columns:
        scores = df['mmse_baseline'].values - df['mmse_followup'].values
        y = (scores >= DECREASE_THRESHOLD).astype(int)
    elif 'moca_baseline' in df.columns and 'moca_followup' in df.columns:
        scores = df['moca_baseline'].values - df['moca_followup'].values
        y = (scores >= DECREASE_THRESHOLD).astype(int)
    else:
        # If no raw scores, assume 'decline_label' exists
        if 'decline_label' in df.columns:
            y = df['decline_label'].values.astype(int)
        else:
            raise ValueError("Cannot compute decline label: missing score columns.")
    
    logger.log("load_features_end", n_features=len(feature_cols), n_samples=len(df), n_decline=int(y.sum()))
    return X, y, feature_cols

class CollinearityTransformer:
    """
    Removes highly correlated features (Pearson > 0.95), keeping the one with higher variance.
    """
    def __init__(self, threshold: float = CORR_THRESHOLD):
        self.threshold = threshold
        self.keep_indices_: Optional[List[int]] = None
    
    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'CollinearityTransformer':
        if X.shape[1] == 0:
            self.keep_indices_ = []
            return self
        
        corr_matrix = calculate_correlation_matrix(X)
        n_features = X.shape[1]
        
        # Mask for upper triangle (excluding diagonal)
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        high_corr_pairs = np.where((corr_matrix >= self.threshold) & mask)
        
        keep = set(range(n_features))
        removed = set()
        
        # Simple greedy removal: for each pair, remove the one with lower variance
        for i, j in zip(high_corr_pairs[0], high_corr_pairs[1]):
            if i in removed or j in removed:
                continue
            
            # Calculate variance for both
            var_i = np.var(X[:, i])
            var_j = np.var(X[:, j])
            
            # Keep the one with higher variance
            if var_i >= var_j:
                removed.add(j)
            else:
                removed.add(i)
        
        self.keep_indices_ = sorted(list(keep - removed))
        return self
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.keep_indices_:
            return np.array([]).reshape(X.shape[0], 0)
        return X[:, self.keep_indices_]
    
    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        self.fit(X, y)
        return self.transform(X)

@log_operation
def train_single_fold(X: np.ndarray, y: np.ndarray, train_idx: List[int], test_idx: List[int], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Train a Random Forest on a single fold with nested feature selection.
    """
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # 1. Collinearity check
    collinearity_step = CollinearityTransformer(threshold=CORR_THRESHOLD)
    X_train_coll = collinearity_step.fit_transform(X_train)
    X_test_coll = collinearity_step.transform(X_test)
    
    if X_train_coll.shape[1] == 0:
        raise ValueError("Collinearity filtering removed all features.")
    
    # 2. Variance Thresholding
    var_thresh = VarianceThreshold(threshold=VAR_THRESHOLD)
    X_train_var = var_thresh.fit_transform(X_train_coll)
    X_test_var = var_thresh.transform(X_test_coll)
    
    if X_train_var.shape[1] == 0:
        raise ValueError("Variance thresholding removed all features.")
    
    # 3. RFE to select <= MAX_FEATURES
    base_rf = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=1)
    rfe = RFE(estimator=base_rf, n_features_to_select=min(MAX_FEATURES, X_train_var.shape[1]), step=1)
    rfe.fit(X_train_var, y_train)
    
    X_train_rfe = rfe.transform(X_train_var)
    X_test_rfe = rfe.transform(X_test_var)
    
    # 4. Train Final RF with Grid Search (Inner Loop)
    # Since we are inside a CV loop, we do a small grid search here
    param_grid = {
        'n_estimators': params.get('n_estimators', [100]),
        'max_depth': params.get('max_depth', [None])
    }
    
    rf_final = RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=1)
    
    # If only 1 combination, skip grid search
    n_combos = len(param_grid['n_estimators']) * len(param_grid['max_depth'])
    if n_combos == 1:
        rf_final.set_params(**{
            'n_estimators': param_grid['n_estimators'][0],
            'max_depth': param_grid['max_depth'][0]
        })
        rf_final.fit(X_train_rfe, y_train)
        best_params = {
            'n_estimators': param_grid['n_estimators'][0],
            'max_depth': param_grid['max_depth'][0]
        }
    else:
        inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
        grid_search = GridSearchCV(
            rf_final, 
            param_grid, 
            cv=inner_cv, 
            scoring='roc_auc', 
            n_jobs=N_JOBS,
            refit=True
        )
        grid_search.fit(X_train_rfe, y_train)
        best_params = grid_search.best_params_
        rf_final = grid_search.best_estimator_
    
    # Evaluate on test set
    y_pred_proba = rf_final.predict_proba(X_test_rfe)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)
    
    return {
        'auc': auc,
        'best_params': best_params,
        'n_features_selected': X_train_rfe.shape[1]
    }

@log_operation
def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray, grid_params: Dict[str, List[Any]]) -> Tuple[List[Dict], Dict[str, Any]]:
    """
    Perform nested cross-validation.
    Outer loop: StratifiedKFold for evaluation.
    Inner loop: GridSearchCV for hyperparameter tuning.
    """
    n_splits = 5
    outer_cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    
    cv_results = []
    all_best_params = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        logger.log("fold_start", fold=fold_idx, n_train=len(train_idx), n_test=len(test_idx))
        
        fold_result = train_single_fold(X, y, train_idx, test_idx, grid_params)
        fold_result['fold'] = fold_idx
        cv_results.append(fold_result)
        all_best_params.append(fold_result['best_params'])
        
        logger.log("fold_end", fold=fold_idx, auc=fold_result['auc'])
    
    # Aggregate results
    mean_auc = np.mean([r['auc'] for r in cv_results])
    std_auc = np.std([r['auc'] for r in cv_results])
    
    # Find most common best params
    from collections import Counter
    param_counts = Counter()
    for p in all_best_params:
        param_counts[tuple(sorted(p.items()))] += 1
    best_overall_params = dict(param_counts.most_common(1)[0][0])
    
    summary = {
        'mean_auc': mean_auc,
        'std_auc': std_auc,
        'n_splits': n_splits,
        'best_overall_params': best_overall_params
    }
    
    return cv_results, summary

@log_operation
def persist_model(X: np.ndarray, y: np.ndarray, model: Any, params: Dict[str, Any], output_path: str):
    """
    Train a final model on the full dataset and save it.
    """
    logger.log("persist_model_start", n_samples=len(y))
    
    # Re-run the full pipeline on full data to get the final model object
    # 1. Collinearity
    collinearity_step = CollinearityTransformer(threshold=CORR_THRESHOLD)
    X_coll = collinearity_step.fit_transform(X)
    
    # 2. Variance
    var_thresh = VarianceThreshold(threshold=VAR_THRESHOLD)
    X_var = var_thresh.fit_transform(X_coll)
    
    # 3. RFE
    base_rf = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=1)
    rfe = RFE(estimator=base_rf, n_features_to_select=min(MAX_FEATURES, X_var.shape[1]), step=1)
    rfe.fit(X_var, y)
    X_rfe = rfe.transform(X_var)
    
    # 4. Final RF
    final_rf = RandomForestClassifier(**params, random_state=RANDOM_SEED, n_jobs=N_JOBS)
    final_rf.fit(X_rfe, y)
    
    # Save components
    joblib.dump({
        'model': final_rf,
        'collinearity': collinearity_step,
        'variance': var_thresh,
        'rfe': rfe,
        'params': params
    }, output_path)
    
    logger.log("persist_model_end", path=output_path)

@log_operation
def write_cv_results(results: List[Dict], summary: Dict, output_path: str):
    """Write CV results to JSON."""
    data = {
        'folds': results,
        'summary': summary
    }
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    logger.log("write_cv_results_end", path=output_path)

@log_operation
def write_model_params(params: Dict, output_path: str):
    """Write final model parameters to JSON."""
    with open(output_path, 'w') as f:
        json.dump(params, f, indent=2)
    logger.log("write_model_params_end", path=output_path)

@log_operation
def main():
    """Main entry point for training."""
    start_time = time.time()
    logger.log("main_start")
    
    # Load data
    # We need to load the eligible subjects list first to ensure we only train on valid data
    eligible_file = Path("data/processed/eligible_subjects.csv")
    if not eligible_file.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {eligible_file}")
    
    eligible_df = pd.read_csv(eligible_file)
    subject_ids = eligible_df['subject_id'].tolist()
    
    if not subject_ids:
        raise ValueError("No eligible subjects found.")
    
    X, y, feature_names = load_features(subject_ids)
    
    # Define grid search parameters
    grid_params = {
        'n_estimators': N_ESTIMATORS_GRID,
        'max_depth': MAX_DEPTH_GRID
    }
    
    # Run nested CV
    cv_results, summary = train_and_evaluate_nested_cv(X, y, grid_params)
    
    # Write results
    cv_results_path = "data/processed/cv_results.json"
    model_params_path = "data/processed/model_params.json"
    model_path = "data/processed/model.pkl"
    
    write_cv_results(cv_results, summary, cv_results_path)
    
    # Write best params
    write_model_params(summary['best_overall_params'], model_params_path)
    
    # Train and persist final model
    persist_model(X, y, None, summary['best_overall_params'], model_path)
    
    elapsed = time.time() - start_time
    logger.log("main_end", elapsed_seconds=elapsed, mean_auc=summary['mean_auc'])
    
    print(f"Training complete. Mean AUC: {summary['mean_auc']:.4f} (+/- {summary['std_auc']:.4f})")
    print(f"Elapsed time: {elapsed:.2f}s")

if __name__ == "__main__":
    main()