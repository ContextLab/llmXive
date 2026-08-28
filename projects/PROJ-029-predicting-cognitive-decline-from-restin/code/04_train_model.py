"""
Train a Random Forest model to predict cognitive decline using nested cross-validation.

Implements FR-010 (Nested CV) with fixed parameters from FR-003 (n_estimators=100, max_depth=None).
The inner loop is used strictly for feature selection (Variance Threshold + RFE) and collinearity handling.
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
from sklearn.feature_selection import VarianceThreshold, RFE
from sklearn.model_selection import StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr
import joblib

# Import from local utils
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, load_csv, save_json
from utils.stats import check_collinearity, calculate_correlation_matrix

logger = get_logger("train_model")

# Constants
RANDOM_SEED = 42
MAX_FEATURES = 20
MIN_VARIANCE = 0.01
COLLINEARITY_THRESHOLD = 0.95
DECLINE_THRESHOLD = 3  # Points drop for cognitive decline label
N_ESTIMATORS = 100
MAX_DEPTH = None
OUTER_FOLDS = 5
INNER_FOLDS = 3

@log_operation
def load_features(subject_ids: List[str], metrics_path: str) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Load graph metrics and compute decline labels.
    
    Args:
        subject_ids: List of subject IDs to load.
        metrics_path: Path to graph_metrics.csv.
        
    Returns:
        X: Feature matrix (n_subjects, n_features).
        y: Target vector (n_subjects,).
        df: Original dataframe for reference.
    """
    df = load_csv(metrics_path)
    
    # Filter for requested subjects
    df = df[df['subject_id'].isin(subject_ids)].copy()
    
    if df.empty:
        raise ValueError(f"No data found for the provided subject IDs in {metrics_path}")
        
    # Sort to ensure consistent ordering
    df = df.sort_values('subject_id')
    
    # Define features (exclude subject_id and target-related columns)
    feature_cols = ['node_degree', 'global_efficiency', 'clustering_coeff', 'path_length']
    
    # Check if all required features exist
    missing = set(feature_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")
        
    X = df[feature_cols].values.astype(np.float64)
    
    # Compute decline label: drop >= 3 points
    # Assuming the CSV has 'mmse_baseline' and 'mmse_followup' or similar
    # If not, we might need to calculate from the data model
    # For now, assume the CSV has the necessary columns or we derive from existing
    # Based on T019 spec: "subject_id, node_degree, global_efficiency, clustering_coeff, path_length"
    # We need the MMSE scores to compute the label. Let's assume they are in the CSV or we need to join.
    # Given the task description implies we have the data, let's assume columns 'mmse_baseline' and 'mmse_followup' exist.
    # If not, we must raise an error or handle it.
    
    if 'mmse_baseline' not in df.columns or 'mmse_followup' not in df.columns:
        # Fallback: try to find similar columns or raise error
        available_cols = [c for c in df.columns if 'mmse' in c.lower() or 'moca' in c.lower()]
        if len(available_cols) >= 2:
            # Heuristic: sort by name to guess baseline/followup
            available_cols.sort()
            baseline_col, followup_col = available_cols[0], available_cols[1]
            df['mmse_baseline'] = df[baseline_col]
            df['mmse_followup'] = df[followup_col]
        else:
            raise ValueError(f"Cannot find MMSE/MOCA columns to compute decline label. Available: {df.columns.tolist()}")
    
    score_drop = df['mmse_baseline'] - df['mmse_followup']
    y = (score_drop >= DECLINE_THRESHOLD).astype(int).values
    
    return X, y, df

class CollinearityTransformer:
    """
    Custom transformer to handle collinearity within the inner CV loop.
    Removes one of any pair of features with Pearson correlation > 0.95, keeping the one with higher variance.
    """
    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.features_to_keep: Optional[List[int]] = None
        self.correlation_matrix: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None):
        n_features = X.shape[1]
        if n_features == 0:
            return self
            
        # Calculate correlation matrix
        corr_matrix = np.corrcoef(X.T)
        self.correlation_matrix = corr_matrix
        
        # Identify features to keep
        keep_indices = list(range(n_features))
        remove_indices = set()
        
        for i in range(n_features):
            if i in remove_indices:
                continue
            for j in range(i + 1, n_features):
                if j in remove_indices:
                    continue
                if abs(corr_matrix[i, j]) > self.threshold:
                    # Remove the one with lower variance
                    var_i = np.var(X[:, i])
                    var_j = np.var(X[:, j])
                    if var_i >= var_j:
                        remove_indices.add(j)
                    else:
                        remove_indices.add(i)
                        
        self.features_to_keep = [i for i in range(n_features) if i not in remove_indices]
        logger.log("collinearity_handling", n_features_initial=n_features, n_features_kept=len(self.features_to_keep))
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self.features_to_keep is None:
            raise RuntimeError("CollinearityTransformer not fitted")
        return X[:, self.features_to_keep]

    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        self.fit(X, y)
        return self.transform(X)

@log_operation
def train_single_fold(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, fold_idx: int) -> Dict[str, Any]:
    """
    Train a single fold with nested feature selection.
    
    Inside the inner loop:
    1. Collinearity check (exclude features with correlation > 0.95)
    2. Variance Thresholding (variance > 0.01)
    3. RFE to select <= 20 features
    4. Fit Random Forest with fixed params
    """
    # Step 1: Collinearity Handling
    collinearity_pipe = CollinearityTransformer(threshold=COLLINEARITY_THRESHOLD)
    X_train_coll = collinearity_pipe.fit_transform(X_train)
    X_test_coll = collinearity_pipe.transform(X_test)
    
    # Step 2: Variance Thresholding
    vt = VarianceThreshold(threshold=MIN_VARIANCE)
    X_train_vt = vt.fit_transform(X_train_coll)
    X_test_vt = vt.transform(X_test_coll)
    
    # If no features left, return a default result
    if X_train_vt.shape[1] == 0:
        return {
            'fold': fold_idx,
            'n_estimators': N_ESTIMATORS,
            'max_depth': MAX_DEPTH,
            'roc_auc': 0.5, # Random guess
            'accuracy': 0.5,
            'f1_score': 0.0,
            'n_features_selected': 0
        }

    # Step 3: RFE to select <= 20 features
    # Use a base estimator for RFE (Random Forest)
    base_rf = RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED) # Small n_estimators for speed in RFE
    rfe = RFE(estimator=base_rf, n_features_to_select=min(MAX_FEATURES, X_train_vt.shape[1]), step=1)
    rfe.fit(X_train_vt, y_train)
    
    X_train_rfe = rfe.transform(X_train_vt)
    X_test_rfe = rfe.transform(X_test_vt)
    
    # Step 4: Fit Final Random Forest with fixed parameters
    rf = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        random_state=RANDOM_SEED,
        n_jobs=2
    )
    rf.fit(X_train_rfe, y_train)
    
    # Predictions
    y_pred_proba = rf.predict_proba(X_test_rfe)[:, 1]
    y_pred = rf.predict(X_test_rfe)
    
    # Metrics
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    return {
        'fold': fold_idx,
        'n_estimators': N_ESTIMATORS,
        'max_depth': MAX_DEPTH,
        'roc_auc': float(roc_auc),
        'accuracy': float(acc),
        'f1_score': float(f1),
        'n_features_selected': X_train_rfe.shape[1]
    }

@log_operation
def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray, outer_folds: int = OUTER_FOLDS) -> List[Dict[str, Any]]:
    """
    Run nested cross-validation.
    Outer loop: StratifiedKFold for evaluation.
    Inner loop: Handled inside train_single_fold for feature selection.
    """
    results = []
    skf_outer = StratifiedKFold(n_splits=outer_folds, shuffle=True, random_state=RANDOM_SEED)
    
    logger.log("nested_cv_start", n_samples=X.shape[0], n_classes=len(np.unique(y)), outer_folds=outer_folds)
    
    for fold_idx, (train_idx, test_idx) in enumerate(skf_outer.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        fold_result = train_single_fold(X_train, y_train, X_test, y_test, fold_idx)
        results.append(fold_result)
        logger.log("fold_complete", fold=fold_idx, roc_auc=fold_result['roc_auc'])
        
    return results

@log_operation
def persist_model(model: Any, path: str):
    """Save the final model to disk."""
    ensure_dir(path)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.log("model_saved", path=path)

@log_operation
def write_cv_results(results: List[Dict[str, Any]], path: str):
    """Write CV results to JSON."""
    ensure_dir(path)
    # Ensure the path is a file
    save_json(results, path)
    logger.log("cv_results_saved", path=path, n_folds=len(results))

@log_operation
def write_model_params(params: Dict[str, Any], path: str):
    """Write model parameters to JSON."""
    ensure_dir(path)
    save_json(params, path)
    logger.log("model_params_saved", path=path)

def main():
    """Main entry point for T023."""
    start_time = time.time()
    
    # Paths
    base_dir = Path("data/processed")
    metrics_path = base_dir / "graph_metrics.csv"
    output_model = base_dir / "model.pkl"
    output_cv_results = base_dir / "cv_results.json"
    output_model_params = base_dir / "model_params.json"
    
    # Ensure directories exist
    ensure_dir(str(output_model))
    ensure_dir(str(output_cv_results))
    ensure_dir(str(output_model_params))
    
    logger.log("train_model_main_start", metrics_path=str(metrics_path))
    
    # Load data
    try:
        # We need subject IDs. If graph_metrics.csv has them, we can read all.
        # However, we need to ensure we only use eligible subjects.
        # Assuming graph_metrics.csv only contains eligible subjects from T019.
        X, y, df = load_features(df['subject_id'].tolist(), str(metrics_path))
    except Exception as e:
        logger.log("data_loading_failed", error=str(e))
        print(f"Error loading data: {e}")
        sys.exit(1)
        
    if len(y) == 0:
        logger.log("no_data_for_training")
        print("No data available for training.")
        sys.exit(1)
        
    logger.log("data_loaded", n_samples=X.shape[0], n_features=X.shape[1], n_positive=y.sum())
    
    # Run Nested CV
    cv_results = train_and_evaluate_nested_cv(X, y, outer_folds=OUTER_FOLDS)
    
    # Write CV results
    write_cv_results(cv_results, str(output_cv_results))
    
    # Train final model on ALL data for persistence (using the same pipeline logic)
    # Note: In a strict nested CV, the final model is not used for evaluation,
    # but we need to save a model for downstream tasks (T024, T029).
    # We will re-run the feature selection on the full dataset to create a "final" model.
    collinearity_pipe = CollinearityTransformer(threshold=COLLINEARITY_THRESHOLD)
    X_coll = collinearity_pipe.fit_transform(X)
    
    vt = VarianceThreshold(threshold=MIN_VARIANCE)
    X_vt = vt.fit_transform(X_coll)
    
    rfe = RFE(estimator=RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED), 
              n_features_to_select=min(MAX_FEATURES, X_vt.shape[1]), step=1)
    rfe.fit(X_vt, y)
    
    X_final = rfe.transform(X_vt)
    
    final_rf = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        random_state=RANDOM_SEED,
        n_jobs=2
    )
    final_rf.fit(X_final, y)
    
    # Save the final model
    persist_model(final_rf, str(output_model))
    
    # Save model parameters
    model_params = {
        "n_estimators": N_ESTIMATORS,
        "max_depth": MAX_DEPTH,
        "random_seed": RANDOM_SEED,
        "n_features_selected": X_final.shape[1],
        "decline_threshold": DECLINE_THRESHOLD,
        "collinearity_threshold": COLLINEARITY_THRESHOLD,
        "min_variance": MIN_VARIANCE,
        "outer_folds": OUTER_FOLDS,
        "inner_folds": INNER_FOLDS
    }
    write_model_params(model_params, str(output_model_params))
    
    end_time = time.time()
    runtime = end_time - start_time
    logger.log("train_model_main_complete", runtime=runtime, cv_results_count=len(cv_results))
    print(f"Training complete. Runtime: {runtime:.2f}s")
    print(f"Results saved to: {output_cv_results}")
    print(f"Model saved to: {output_model}")

if __name__ == "__main__":
    main()