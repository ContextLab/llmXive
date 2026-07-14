from __future__ import annotations

import json
import os
import sys
import time
import pickle
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from joblib import Parallel, delayed, dump, load
from scipy.stats import pearsonr
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.model_selection import (
    GridSearchCV,
    KFold,
    cross_val_score,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score
from sklearn.base import BaseEstimator, TransformerMixin
from scipy.stats import pearsonr
from joblib import Parallel, delayed

from utils.logger import get_logger, log_operation
from utils.io import save_json, save_pickle, load_csv
from utils.stats import calculate_correlation_matrix, calculate_feature_variance

# Constants
RANDOM_SEED = 42
GRAPH_METRICS_PATH = "data/processed/graph_metrics.csv"
ELIGIBLE_SUBJECTS_PATH = "data/processed/eligible_subjects.csv"
MODEL_OUTPUT_PATH = "data/processed/model.pkl"
CV_RESULTS_PATH = "data/processed/cv_results.json"
MODEL_PARAMS_PATH = "data/processed/model_params.json"

logger = get_logger("train_model")

def load_eligible_subjects(path: str = ELIGIBLE_SUBJECTS_PATH) -> List[str]:
    """Load list of eligible subject IDs."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Eligible subjects file not found: {path}")
    df = pd.read_csv(path)
    # Assume column 'subject_id' or first column
    col = 'subject_id' if 'subject_id' in df.columns else df.columns[0]
    return df[col].astype(str).tolist()

def load_features(path: str = GRAPH_METRICS_PATH) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load graph metrics, define decline label (drop >= 3 points),
    and return X, y, feature_names.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Graph metrics file not found: {path}")
    
    df = pd.read_csv(path)
    
    # Identify columns: subject_id, mmse_t1, mmse_t2 (or similar), and metric columns
    # Heuristic: numeric columns are features, specific columns are labels
    # Based on typical pipeline output: subject_id, mmse_baseline, mmse_followup, metric1, metric2...
    
    # Check for required columns
    required_cols = ['subject_id', 'mmse_baseline', 'mmse_followup']
    if not all(col in df.columns for col in required_cols):
        # Fallback: try generic names if specific ones aren't found
        # Look for columns containing 'mmse' or 'moca'
        mmse_cols = [c for c in df.columns if 'mmse' in c.lower()]
        if len(mmse_cols) >= 2:
            mmse_cols = sorted(mmse_cols) # Sort to assume order
            df['mmse_baseline'] = df[mmse_cols[0]]
            df['mmse_followup'] = df[mmse_cols[1]]
        else:
            raise ValueError(f"Cannot find MMSE columns in {path}. Found: {df.columns.tolist()}")

    # Define decline label: drop >= 3 points
    # Decline = 1 if (baseline - followup) >= 3, else 0
    # Handle NaNs by dropping rows
    df = df.dropna(subset=['mmse_baseline', 'mmse_followup'])
    df['decline'] = (df['mmse_baseline'] - df['mmse_followup']) >= 3
    df['decline'] = df['decline'].astype(int)

    # Feature columns: all numeric columns except the label and subject_id
    # Exclude subject_id, mmse_baseline, mmse_followup, decline
    exclude_cols = ['subject_id', 'mmse_baseline', 'mmse_followup', 'decline']
    feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if len(feature_cols) == 0:
        raise ValueError(f"No feature columns found in {path}. Exclude cols: {exclude_cols}, All cols: {df.columns.tolist()}")

    X = df[feature_cols].values
    y = df['decline'].values
    feature_names = feature_cols

    logger.log("load_features", 
               operation="load_features", 
               subjects=len(X), 
               features=len(feature_names), 
               decline_rate=float(np.mean(y)))
    
    return X, y, feature_names

class CollinearityTransformer(BaseEstimator, TransformerMixin):
    """
    Remove features with Pearson correlation > 0.95, keeping the one with higher variance.
    """
    def __init__(self, threshold=0.95):
        self.threshold = threshold
        self.mask_ = None

    def fit(self, X, y=None):
        if X.shape[1] < 2:
            self.keep_indices_ = np.arange(X.shape[1])
            return self

        corr_matrix = np.corrcoef(X, rowvar=False)
        upper = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        high_corr = np.abs(corr_matrix[upper]) > self.threshold
        
        # Find indices in upper triangle that are high correlation
        rows, cols = np.where(high_corr)
        # Map back to full matrix indices
        # This is a bit tricky with triu, easier to just iterate
        
        remove_indices = set()
        n_features = X.shape[1]
        variances = np.var(X, axis=0)
        
        # Simple iterative removal
        active_indices = list(range(n_features))
        while True:
            changed = False
            if len(active_indices) < 2:
                break
            
            sub_corr = corr_matrix[np.ix_(active_indices, active_indices)]
            sub_high = np.abs(sub_corr) > self.threshold
            np.fill_diagonal(sub_high, False)
            
            for i in range(len(active_indices)):
                if any(sub_high[i]):
                    # Remove the one with lower variance among the correlated pair
                    # Find the first correlated partner
                    partner_idx = active_indices[i + np.argmax(sub_high[i])]
                    curr_idx = active_indices[i]
                    
                    if variances[partner_idx] > variances[curr_idx]:
                        remove_indices.add(curr_idx)
                    else:
                        remove_indices.add(partner_idx)
                    changed = True
                    break # Restart check
            
            if not changed:
                break
        
        self.keep_indices_ = np.array([i for i in range(n_features) if i not in remove_indices])
        return self

    def transform(self, X, y=None):
        return X[:, self.keep_indices_]

def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """
    Perform Nested CV with Grid Search inside.
    Outer: Stratified K-Fold (5 folds)
    Inner: Grid Search on n_estimators and max_depth
    Inside Inner: Collinearity check, Variance Threshold, RFE (<=20 features)
    """
    logger.log("train_and_evaluate_nested_cv", operation="start_nested_cv")

    # Grid Search Parameters
    param_grid = {
        'rf__n_estimators': [50, 100, 200],
        'rf__max_depth': [5, 10, None]
    }

    # Outer CV
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    
    # Pipeline definition
    # Steps: Collinearity -> Variance Threshold -> RFE -> RF
    pipe = Pipeline([
        ('collinearity', CollinearityTransformer(threshold=0.95)),
        ('variance', VarianceThreshold(threshold=0.01)),
        ('rfe', RFE(estimator=RandomForestClassifier(random_state=RANDOM_SEED), n_features_to_select=20)),
        ('rf', RandomForestClassifier(random_state=RANDOM_SEED))
    ])

    # Inner CV for Grid Search
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
    grid_search = GridSearchCV(
        pipe, 
        param_grid, 
        cv=inner_cv, 
        scoring='roc_auc',
        n_jobs=2,
        refit=True
    )

    cv_results = []
    best_params_per_fold = []

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
            logger.log("train_and_evaluate_nested_cv", 
                       operation="fold_skipped", 
                       fold=fold_idx, 
                       reason="Class imbalance in fold")
            continue

        grid_search.fit(X_train, y_train)
        
        y_pred_proba = grid_search.predict_proba(X_test)[:, 1]
        try:
            auc = roc_auc_score(y_test, y_pred_proba)
        except ValueError:
            auc = 0.0 # Handle edge case where all labels are same in test set

        cv_results.append({
            "fold": fold_idx,
            "auc": float(auc),
            "best_params": grid_search.best_params_
        })
        best_params_per_fold.append(grid_search.best_params_)

    # Aggregate results
    mean_auc = np.mean([r['auc'] for r in cv_results])
    std_auc = np.std([r['auc'] for r in cv_results])
    
    # Determine overall best params (most frequent or best mean)
    # For simplicity, take the best params from the fold with highest AUC
    best_fold_idx = np.argmax([r['auc'] for r in cv_results])
    final_params = best_params_per_fold[best_fold_idx]

    return {
        "cv_results": cv_results,
        "mean_auc": float(mean_auc),
        "std_auc": float(std_auc),
        "final_params": final_params
    }

def persist_model(X: np.ndarray, y: np.ndarray, feature_names: List[str], params: Dict[str, Any]) -> str:
    """
    Train final model on full data with best params and save it.
    """
    logger.log("persist_model", operation="training_final_model")
    
    # Reconstruct pipeline with best params
    pipe = Pipeline([
        ('collinearity', CollinearityTransformer(threshold=0.95)),
        ('variance', VarianceThreshold(threshold=0.01)),
        ('rfe', RFE(estimator=RandomForestClassifier(random_state=RANDOM_SEED), n_features_to_select=20)),
        ('rf', RandomForestClassifier(
            n_estimators=params['rf__n_estimators'],
            max_depth=params['rf__max_depth'],
            random_state=RANDOM_SEED
        ))
    ])
    
    pipe.fit(X, y)
    
    model_artifact = {
        "model": pipe,
        "feature_names": feature_names,
        "params": params,
        "seed": RANDOM_SEED
    }
    
    save_pickle(model_artifact, MODEL_OUTPUT_PATH)
    logger.log("persist_model", operation="saved_model", path=MODEL_OUTPUT_PATH)
    return MODEL_OUTPUT_PATH

def write_cv_results(results: Dict[str, Any], path: str = CV_RESULTS_PATH) -> None:
    save_json(results, path)
    logger.log("write_cv_results", operation="saved_cv_results", path=path)

def write_model_params(params: Dict[str, Any], path: str = MODEL_PARAMS_PATH) -> None:
    save_json(params, path)
    logger.log("write_model_params", operation="saved_model_params", path=path)

@log_operation("train_model")
def main():
    start_time = time.time()
    logger.log("main", operation="start_training")

    try:
        # Load data
        X, y, feature_names = load_features()
        logger.log("main", operation="data_loaded", shape=X.shape)

        if len(y) == 0:
            raise ValueError("No eligible subjects with valid labels found.")

        # Train with Nested CV
        results = train_and_evaluate_nested_cv(X, y, feature_names)
        
        # Write CV results
        write_cv_results(results)

        # Persist final model
        persist_model(X, y, feature_names, results['final_params'])

        # Write model params
        write_model_params(results['final_params'])

        elapsed = time.time() - start_time
        logger.log("main", operation="completed", elapsed_seconds=elapsed)
        
        print(f"Training complete. Mean AUC: {results['mean_auc']:.4f} (+/- {results['std_auc']:.4f})")
        print(f"Elapsed time: {elapsed:.2f} seconds")
        print(f"Model saved to: {MODEL_OUTPUT_PATH}")

    except Exception as e:
        logger.log("main", operation="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()