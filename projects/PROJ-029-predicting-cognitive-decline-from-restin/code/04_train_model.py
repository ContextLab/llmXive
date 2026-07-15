"""
Train a Random Forest classifier with nested cross-validation to predict cognitive decline.

This script implements the core modeling pipeline for User Story 2:
- Defines decline label (drop >= 3 points in MMSE/MOCA)
- Implements Nested CV (Outer K-fold, Inner Grid Search)
- Performs feature selection inside the inner loop:
  1. Collinearity check (exclude features with correlation > 0.95)
  2. Variance Thresholding (variance > 0.01)
  3. RFE to select <= 20 features
- Grid Search: n_estimators {50, 100, 200}, max_depth {5, 10, None}

Outputs:
  - data/processed/model.pkl: Trained Random Forest model
  - data/processed/cv_results.json: Full nested CV results
  - data/processed/model_params.json: Best hyperparameters
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
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from scipy.stats import pearsonr

# Local imports matching API surface
from utils.logger import get_logger, log_operation
from utils.stats import check_collinearity, calculate_correlation_matrix, filter_low_variance_features
from utils.io import ensure_dir, save_json, save_pickle, load_csv, load_json

logger = get_logger("train_model")

# Constants
RANDOM_SEED = 42
OUTSIDE_FOLDS = 5
INNER_FOLDS = 3
MAX_FEATURES = 20
CORR_THRESHOLD = 0.95
VAR_THRESHOLD = 0.01

# Grid search parameters
PARAM_GRID = {
    'randomforestclassifier__n_estimators': [50, 100, 200],
    'randomforestclassifier__max_depth': [5, 10, None]
}

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"

ELIGIBLE_SUBJECTS_PATH = DATA_PROCESSED / "eligible_subjects.csv"
GRAPH_METRICS_PATH = DATA_PROCESSED / "graph_metrics.csv"
MODEL_PATH = DATA_PROCESSED / "model.pkl"
CV_RESULTS_PATH = DATA_PROCESSED / "cv_results.json"
MODEL_PARAMS_PATH = DATA_PROCESSED / "model_params.json"

class CollinearityTransformer(BaseEstimator, TransformerMixin):
    """Transformer to remove highly correlated features (correlation > threshold).
    
    Keeps the feature with higher variance when a pair is correlated.
    """
    
    def __init__(self, threshold: float = CORR_THRESHOLD):
        self.threshold = threshold
        self.features_to_keep: List[int] = []
    
    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "CollinearityTransformer":
        if X.shape[1] == 0:
            self.features_to_keep = []
            return self
        
        # Calculate correlation matrix
        corr_matrix = calculate_correlation_matrix(X)
        n_features = X.shape[1]
        
        # Track which features to drop
        drop_indices = set()
        
        # Check upper triangle for correlations
        for i in range(n_features):
            if i in drop_indices:
                continue
            for j in range(i + 1, n_features):
                if j in drop_indices:
                    continue
                
                # Get correlation value (handle NaNs)
                corr_val = corr_matrix[i, j]
                if np.isnan(corr_val):
                    continue
                
                if abs(corr_val) > self.threshold:
                    # Keep the one with higher variance
                    var_i = np.var(X[:, i])
                    var_j = np.var(X[:, j])
                    
                    if var_i >= var_j:
                        drop_indices.add(j)
                    else:
                        drop_indices.add(i)
        
        self.features_to_keep = [i for i in range(n_features) if i not in drop_indices]
        return self
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        if len(self.features_to_keep) == 0:
            return np.empty((X.shape[0], 0))
        return X[:, self.features_to_keep]
    
    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        return self.fit(X, y).transform(X)

def load_features() -> Tuple[np.ndarray, np.ndarray, List[str], List[str]]:
    """Load features and labels from graph metrics CSV.
    
    Returns:
        X: Feature matrix (n_subjects, n_features)
        y: Labels (n_subjects,)
        feature_names: List of feature column names
        subject_ids: List of subject IDs
    """
    if not GRAPH_METRICS_PATH.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {GRAPH_METRICS_PATH}")
    
    df = load_csv(GRAPH_METRICS_PATH)
    
    # Load eligible subjects to ensure we only use those with valid labels
    if not ELIGIBLE_SUBJECTS_PATH.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")
    
    eligible_df = load_csv(ELIGIBLE_SUBJECTS_PATH)
    eligible_ids = set(eligible_df['subject_id'].tolist())
    
    # Filter to eligible subjects
    df = df[df['subject_id'].isin(eligible_ids)]
    
    if df.empty:
        raise ValueError("No eligible subjects found in graph metrics")
    
    # Calculate decline label: drop >= 3 points
    # Assuming columns: mmse_t1, mmse_t2, moca_t1, moca_t2
    # Use whichever is available
    
    # Try to compute decline
    decline_scores = []
    subject_ids = []
    
    for idx, row in df.iterrows():
        sid = row['subject_id']
        
        # Determine decline score (prefer MMSE if available, else MOCA)
        if 'mmse_t1' in row and 'mmse_t2' in row:
            t1 = row['mmse_t1']
            t2 = row['mmse_t2']
            if pd.isna(t1) or pd.isna(t2):
                # Try MOCA
                if 'moca_t1' in row and 'moca_t2' in row:
                    t1 = row['moca_t1']
                    t2 = row['moca_t2']
        
        if pd.isna(t1) or pd.isna(t2):
            # Skip subjects without valid scores
            continue
        
        decline = t1 - t2  # Positive means decline
        decline_scores.append(1 if decline >= 3 else 0)
        subject_ids.append(sid)
    
    if len(decline_scores) == 0:
        raise ValueError("No subjects with valid decline scores found")
    
    # Extract feature columns (exclude subject_id and any label columns)
    exclude_cols = ['subject_id', 'mmse_t1', 'mmse_t2', 'moca_t1', 'moca_t2', 'decline']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_cols].values.astype(np.float64)
    y = np.array(decline_scores)
    
    # Align subject_ids with X, y
    df = df[df['subject_id'].isin(subject_ids)].reset_index(drop=True)
    subject_ids = df['subject_id'].tolist()
    
    logger.log("load_features", subjects=len(subject_ids), features=len(feature_cols))
    
    return X, y, feature_cols, subject_ids

def train_single_fold(X_train: np.ndarray, y_train: np.ndarray, 
                     X_test: np.ndarray, y_test: np.ndarray,
                     param_grid: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
    """Train a single fold with nested feature selection and grid search.
    
    Inside the inner loop:
    1. Collinearity check
    2. Variance thresholding
    3. RFE to select <= 20 features
    4. Grid search for Random Forest
    
    Returns:
        model: Trained pipeline
        cv_results: Inner CV results
    """
    
    # Create pipeline with all preprocessing steps
    pipeline = Pipeline([
        ('collinearity', CollinearityTransformer(threshold=CORR_THRESHOLD)),
        ('variance', VarianceThreshold(threshold=VAR_THRESHOLD)),
        ('rfe', RFE(estimator=RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED), 
                    n_features_to_select=MAX_FEATURES)),
        ('randomforestclassifier', RandomForestClassifier(random_state=RANDOM_SEED))
    ])
    
    # Inner cross-validation for grid search
    inner_cv = StratifiedKFold(n_splits=INNER_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    
    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=inner_cv,
        scoring='roc_auc',
        n_jobs=2,
        return_train_score=True
    )
    
    grid_search.fit(X_train, y_train)
    
    # Get best model
    best_model = grid_search.best_estimator_
    
    # Extract inner CV results
    inner_results = {
        'best_params': grid_search.best_params_,
        'best_score': grid_search.best_score_,
        'cv_results': grid_search.cv_results_
    }
    
    return best_model, inner_results

def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray,
                                 param_grid: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run nested cross-validation.
    
    Outer loop: Stratified K-fold for evaluation
    Inner loop: Grid search with feature selection
    
    Returns:
        outer_results: List of results for each outer fold
        aggregated_results: Aggregated performance metrics
    """
    
    outer_cv = StratifiedKFold(n_splits=OUTSIDE_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    outer_results = []
    
    all_predictions = []
    all_true = []
    
    start_time = time.time()
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        logger.log("fold_start", fold=fold_idx, train_size=len(y_train), test_size=len(y_test))
        
        # Train model with nested CV
        model, inner_results = train_single_fold(X_train, y_train, X_test, y_test, param_grid)
        
        # Evaluate on test set
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        y_pred = (y_pred_proba >= 0.5).astype(int)
        
        # Calculate metrics
        try:
            roc_auc = roc_auc_score(y_test, y_pred_proba)
        except ValueError:
            roc_auc = 0.5  # Fallback for single class
        
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        fold_result = {
            'fold': fold_idx,
            'train_size': len(y_train),
            'test_size': len(y_test),
            'roc_auc': roc_auc,
            'accuracy': accuracy,
            'f1_score': f1,
            'best_params': inner_results['best_params'],
            'inner_cv_best_score': inner_results['best_score']
        }
        
        outer_results.append(fold_result)
        all_predictions.extend(y_pred_proba.tolist())
        all_true.extend(y_test.tolist())
        
        logger.log("fold_complete", fold=fold_idx, roc_auc=roc_auc)
    
    elapsed_time = time.time() - start_time
    
    # Calculate aggregated metrics
    avg_roc_auc = np.mean([r['roc_auc'] for r in outer_results])
    avg_accuracy = np.mean([r['accuracy'] for r in outer_results])
    avg_f1 = np.mean([r['f1_score'] for r in outer_results])
    
    # Overall ROC-AUC from all predictions
    try:
        overall_roc_auc = roc_auc_score(all_true, all_predictions)
    except ValueError:
        overall_roc_auc = 0.5
    
    aggregated_results = {
        'total_time_seconds': elapsed_time,
        'n_folds': OUTSIDE_FOLDS,
        'mean_roc_auc': avg_roc_auc,
        'std_roc_auc': np.std([r['roc_auc'] for r in outer_results]),
        'mean_accuracy': avg_accuracy,
        'mean_f1_score': avg_f1,
        'overall_roc_auc': overall_roc_auc,
        'best_params': outer_results[0]['best_params'] if outer_results else {}
    }
    
    return outer_results, aggregated_results

def persist_model(model: Any, output_path: Path) -> None:
    """Save the trained model to disk."""
    ensure_dir(output_path)
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    logger.log("persist_model", path=str(output_path))

def write_cv_results(outer_results: List[Dict[str, Any]], 
                    aggregated_results: Dict[str, Any],
                    output_path: Path) -> None:
    """Write CV results to JSON."""
    ensure_dir(output_path)
    data = {
        'fold_results': outer_results,
        'aggregated_metrics': aggregated_results
    }
    save_json(data, output_path)
    logger.log("write_cv_results", path=str(output_path), n_folds=len(outer_results))

def write_model_params(aggregated_results: Dict[str, Any], output_path: Path) -> None:
    """Write best model parameters to JSON."""
    ensure_dir(output_path)
    save_json(aggregated_results, output_path)
    logger.log("write_model_params", path=str(output_path))

@log_operation("train_model_main")
def main() -> int:
    """Main entry point for model training."""
    start_time = time.time()
    
    logger.log("train_model_main", operation="start", seed=RANDOM_SEED)
    
    try:
        # Load data
        X, y, feature_names, subject_ids = load_features()
        
        if X.shape[0] < 10:
            logger.log("train_model_main", warning="Insufficient samples for training", n_samples=X.shape[0])
            # Still proceed but warn
        
        logger.log("data_loaded", n_samples=X.shape[0], n_features=X.shape[1])
        
        # Run nested CV
        outer_results, aggregated_results = train_and_evaluate_nested_cv(X, y, PARAM_GRID)
        
        # Get the best model from the last fold (or retrain on all data if needed)
        # For simplicity, we'll use the model from the last fold
        # In a production setting, you might want to retrain on all data
        
        # Retrain on full data for final model
        full_model, _ = train_single_fold(X, y, X, y, PARAM_GRID)
        
        # Save outputs
        persist_model(full_model, MODEL_PATH)
        write_cv_results(outer_results, aggregated_results, CV_RESULTS_PATH)
        write_model_params(aggregated_results, MODEL_PARAMS_PATH)
        
        elapsed_time = time.time() - start_time
        
        logger.log("train_model_main", operation="complete", 
                  time_seconds=elapsed_time, 
                  roc_auc=aggregated_results['mean_roc_auc'])
        
        print(f"Training complete. ROC-AUC: {aggregated_results['mean_roc_auc']:.4f}")
        print(f"Results saved to: {CV_RESULTS_PATH}")
        print(f"Model saved to: {MODEL_PATH}")
        
        return 0
        
    except Exception as e:
        logger.log("train_model_main", operation="error", error=str(e))
        print(f"Error during training: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
