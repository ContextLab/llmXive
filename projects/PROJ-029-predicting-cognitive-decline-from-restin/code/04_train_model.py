"""
Task T023: Train predictive model for cognitive decline using nested CV.

Implements:
- Decline label definition (drop >= 3 points)
- Nested Cross-Validation (Outer K-Fold, Inner Grid Search)
- Feature Selection inside inner loop:
    1. Collinearity check (Pearson > 0.95 -> keep higher variance)
    2. Variance Thresholding (> 0.01)
    3. RFE (select <= 20 features)
- Random Forest with Grid Search (n_estimators: {50, 100, 200}, max_depth: {5, 10, None})
- Outputs: model.pkl, cv_results.json, model_params.json
"""
from __future__ import annotations

import json
import os
import sys
import time
import pickle
from pathlib import Path
from typing import List, Tuple, Any, Dict, Optional

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
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score

# Import project utilities from the API surface
# Note: utils.logger is preferred, but 04_train_model.py in the API surface
# imports from utils.io. We will use utils.io for data loading.
from utils.io import load_csv, save_pickle, load_json, save_json
from utils.logger import get_logger, log_operation
from utils.stats import check_collinearity, calculate_correlation_matrix

# Constants
RANDOM_SEED = 42
OUTSIDE_DIR = Path("data/processed")
MODEL_FILE = OUTSIDE_DIR / "model.pkl"
CV_RESULTS_FILE = OUTSIDE_DIR / "cv_results.json"
MODEL_PARAMS_FILE = OUTSIDE_DIR / "model_params.json"
ELIGIBLE_SUBJECTS_FILE = OUTSIDE_DIR / "eligible_subjects.csv"
GRAPH_METRICS_FILE = OUTSIDE_DIR / "graph_metrics.csv"

# Grid Search Parameters (as per T023 spec)
N_ESTIMATORS_GRID = [50, 100, 200]
MAX_DEPTH_GRID = [5, 10, None]
MAX_FEATURES_RFE = 20
CORRELATION_THRESHOLD = 0.95
VARIANCE_THRESHOLD = 0.01
DECLINE_CUTOFF = 3

logger = get_logger("train_model")


class CollinearityFilter(BaseEstimator, TransformerMixin):
    """
    Removes features with Pearson correlation > threshold.
    Keeps the feature with higher variance.
    """

    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.mask_ = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None):
        if X.shape[1] == 0:
            return self
        
        corr_matrix = np.corrcoef(X.T)
        n_features = X.shape[1]
        self.mask_ = np.ones(n_features, dtype=bool)

        for i in range(n_features):
            if not self.mask_[i]:
                continue
            for j in range(i + 1, n_features):
                if not self.mask_[j]:
                    continue
                if np.abs(corr_matrix[i, j]) > self.threshold:
                    # Keep the one with higher variance
                    var_i = np.var(X[:, i])
                    var_j = np.var(X[:, j])
                    if var_i >= var_j:
                        self.mask_[j] = False
                    else:
                        self.mask_[i] = False
                        break
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if X.shape[1] == 0:
            return X
        return X[:, self.mask_]


def load_eligible_subjects() -> List[str]:
    """Load list of eligible subject IDs."""
    if not ELIGIBLE_SUBJECTS_FILE.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_FILE}")
    df = pd.read_csv(ELIGIBLE_SUBJECTS_FILE)
    return df["subject_id"].tolist()


def load_features() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load graph metrics and compute labels.
    Returns: X (features), y (labels), feature_names
    """
    if not GRAPH_METRICS_FILE.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {GRAPH_METRICS_FILE}")
    
    df = pd.read_csv(GRAPH_METRICS_FILE)
    
    # Identify label columns (assuming 'mmse_baseline', 'mmse_followup' or similar)
    # Based on T017/T019 context, we need to find the score columns.
    # We look for columns containing 'mmse' or 'moca' and 'baseline'/'followup'.
    # For robustness, we assume the first two numeric score columns found are the scores.
    score_cols = [col for col in df.columns if 'score' in col.lower() or 'mmse' in col.lower()]
    
    if len(score_cols) < 2:
        # Fallback: assume specific column names if standard ones exist
        if 'mmse_baseline' in df.columns and 'mmse_followup' in df.columns:
            score_cols = ['mmse_baseline', 'mmse_followup']
        elif 'moca_baseline' in df.columns and 'moca_followup' in df.columns:
            score_cols = ['moca_baseline', 'moca_followup']
        else:
            raise ValueError(f"Could not identify score columns in {GRAPH_METRICS_FILE}. Found: {list(df.columns)}")
    
    if score_cols[0] not in df.columns or score_cols[1] not in df.columns:
        # Try moca if mmse not found
        if 'moca_baseline' in df.columns and 'moca_followup' in df.columns:
            score_cols = ['moca_baseline', 'moca_followup']
        else:
             raise ValueError(f"Specific score columns not found: {score_cols}")

    # Compute decline
    # Handle potential NaNs
    baseline = df[score_cols[0]].fillna(0)
    followup = df[score_cols[1]].fillna(0)
    
    decline = baseline - followup
    y = (decline >= DECLINE_CUTOFF).astype(int)
    
    # Features are all numeric columns except subject_id and score columns
    feature_cols = [col for col in df.columns 
                    if col not in ['subject_id'] + score_cols 
                    and pd.api.types.is_numeric_dtype(df[col])]
    
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found in graph metrics.")
    
    X = df[feature_cols].values
    return X, y.values, feature_cols


def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """
    Perform Nested Cross-Validation.
    Outer: K-Fold for evaluation.
    Inner: Grid Search with Feature Selection pipeline.
    """
    logger.log("Starting Nested CV", n_jobs=2)
    
    # Outer CV
    outer_cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    outer_scores = []
    all_predictions = []
    all_true = []
    
    # Store best params from the last fold or aggregate
    best_params_overall = {}
    
    # Inner Pipeline components
    # 1. Collinearity Filter
    # 2. Variance Threshold
    # 3. RFE
    # 4. RandomForest
    
    param_grid = {
        'rf__n_estimators': N_ESTIMATORS_GRID,
        'rf__max_depth': MAX_DEPTH_GRID
    }
    
    # We need to wrap the pipeline so RFE and VarianceThreshold are part of the CV
    # But RFE requires an estimator. We use a dummy RF for RFE, then GridSearch over RF.
    # Actually, standard approach: Pipeline -> [Scaler, VarThresh, Collin, RFE, RF]
    # RFE needs an estimator. We can use a temporary RF for RFE estimation.
    
    # To handle the inner loop correctly:
    # We create a pipeline where RFE uses a base estimator, and GridSearch tunes the final RF.
    # However, tuning the final RF inside RFE is tricky.
    # Alternative: Custom CV loop or use sklearn's Pipeline with RFE and tune the RF at the end.
    
    # Strategy:
    # Pipeline: Scaler -> CollinearityFilter -> VarianceThreshold -> RFE -> RandomForest
    # RFE estimator: RandomForest(n_estimators=100) (fixed for RFE)
    # GridSearch tunes the final RandomForest parameters.
    
    base_rf = RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=1) # RFE needs n_jobs=1 usually
    
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('collinearity', CollinearityFilter(threshold=CORRELATION_THRESHOLD)),
        ('var_thresh', VarianceThreshold(threshold=VARIANCE_THRESHOLD)),
        ('rfe', RFE(estimator=base_rf, n_features_to_select=MAX_FEATURES_RFE)),
        ('rf', RandomForestClassifier(random_state=RANDOM_SEED))
    ])
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Inner CV for Hyperparameter Tuning
        inner_cv = KFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
        
        grid_search = GridSearchCV(
            pipe,
            param_grid,
            cv=inner_cv,
            scoring='roc_auc',
            n_jobs=2,
            refit=True
        )
        
        grid_search.fit(X_train, y_train)
        
        # Evaluate on outer test set
        y_pred = grid_search.predict(X_test)
        y_proba = grid_search.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        try:
            auc = roc_auc_score(y_test, y_proba)
        except ValueError:
            auc = 0.0 # Handle edge case of single class
        
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        outer_scores.append(auc)
        all_predictions.extend(y_pred)
        all_true.extend(y_test)
        
        if fold_idx == len(outer_cv.split(X)) - 1:
            best_params_overall = grid_search.best_params_
        
        logger.log(f"Fold {fold_idx} complete", auc=auc, acc=acc, f1=f1)
    
    # Train final model on full data using best params
    # We re-run the pipeline with the best params on the full dataset
    final_pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('collinearity', CollinearityFilter(threshold=CORRELATION_THRESHOLD)),
        ('var_thresh', VarianceThreshold(threshold=VARIANCE_THRESHOLD)),
        ('rfe', RFE(estimator=RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=1), n_features_to_select=MAX_FEATURES_RFE)),
        ('rf', RandomForestClassifier(random_state=RANDOM_SEED, **best_params_overall))
    ])
    
    final_pipe.fit(X, y)
    
    return {
        "mean_auc": float(np.mean(outer_scores)),
        "std_auc": float(np.std(outer_scores)),
        "all_auc": outer_scores,
        "best_params": best_params_overall,
        "final_model": final_pipe,
        "feature_names_after_selection": None # Will be updated after fitting
    }


def persist_model(model: Any, path: Path):
    """Save model to disk."""
    logger.log("Persisting model", path=str(path))
    dump(model, path)


def write_model_params(params: Dict[str, Any], path: Path):
    """Save model parameters to JSON."""
    # Convert numpy types to python types for JSON
    serializable_params = {}
    for k, v in params.items():
        if isinstance(v, (np.integer, np.floating)):
            serializable_params[k] = float(v)
        elif isinstance(v, np.ndarray):
            serializable_params[k] = v.tolist()
        else:
            serializable_params[k] = v
    
    with open(path, 'w') as f:
        json.dump(serializable_params, f, indent=2)


def write_performance_report(results: Dict[str, Any], path: Path):
    """Write performance report to JSON."""
    report = {
        "mean_auc": results["mean_auc"],
        "std_auc": results["std_auc"],
        "outer_folds_auc": results["all_auc"],
        "best_params": results["best_params"]
    }
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)


@log_operation("train_model")
def main():
    start_time = time.time()
    
    # Ensure output directory exists
    OUTSIDE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data
    logger.log("Loading eligible subjects")
    subjects = load_eligible_subjects()
    logger.log("Subjects loaded", count=len(subjects))
    
    if len(subjects) == 0:
        raise ValueError("No eligible subjects found. Cannot train model.")
    
    logger.log("Loading features and labels")
    X, y, feature_names = load_features()
    logger.log("Features loaded", shape=X.shape, n_samples=len(y))
    
    if X.shape[0] != len(y):
        raise ValueError("Mismatch between features and labels.")
    
    # 2. Train Model with Nested CV
    logger.log("Starting Nested CV training")
    results = train_and_evaluate_nested_cv(X, y, feature_names)
    
    # 3. Save Artifacts
    persist_model(results["final_model"], MODEL_FILE)
    
    # Write model params
    write_model_params(results["best_params"], MODEL_PARAMS_FILE)
    
    # Write performance report
    write_performance_report(results, CV_RESULTS_FILE)
    
    elapsed = time.time() - start_time
    logger.log("Training complete", elapsed_seconds=elapsed, output_files=[
        str(MODEL_FILE), str(CV_RESULTS_FILE), str(MODEL_PARAMS_FILE)
    ])
    
    print(f"Training complete. Runtime: {elapsed:.2f}s")
    print(f"Mean AUC: {results['mean_auc']:.4f} (+/- {results['std_auc']:.4f})")
    print(f"Model saved to {MODEL_FILE}")
    
    return 0


if __name__ == "__main__":
    main()
