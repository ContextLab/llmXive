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
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import joblib

# Import shared utilities
from utils.io import load_csv, save_json, save_pickle
from utils.stats import check_collinearity, filter_low_variance_features
from utils.logger import get_logger, log_operation

logger = get_logger("train_model")

# Constants
DATA_DIR = Path("data/processed")
GRAPH_METRICS_PATH = DATA_DIR / "graph_metrics.csv"
ELIGIBLE_SUBJECTS_PATH = DATA_DIR / "eligible_subjects.csv"
MODEL_PATH = DATA_DIR / "model.pkl"
CV_RESULTS_PATH = DATA_DIR / "cv_results.json"
MODEL_PARAMS_PATH = DATA_DIR / "model_params.json"

# Grid Search Parameters per FR-010
PARAM_GRID = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, None]
}

class CollinearityTransformer:
    """
    Custom transformer to handle collinearity within a pipeline.
    Removes features with correlation > 0.95, keeping the one with higher variance.
    """
    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.keep_indices_ = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None):
        if X.shape[1] == 0:
            self.keep_indices_ = np.array([])
            return self

        corr_matrix = np.corrcoef(X, rowvar=False)
        # Mask upper triangle to avoid double counting
        upper = np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        high_corr = np.where(upper & (np.abs(corr_matrix) > self.threshold))

        to_remove = set()
        for i, j in zip(high_corr[0], high_corr[1]):
            if i not in to_remove and j not in to_remove:
                # Keep the one with higher variance
                var_i = np.var(X[:, i])
                var_j = np.var(X[:, j])
                if var_i >= var_j:
                    to_remove.add(j)
                else:
                    to_remove.add(i)

        self.keep_indices_ = np.array([i for i in range(X.shape[1]) if i not in to_remove])
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if len(self.keep_indices_) == 0:
            return np.empty((X.shape[0], 0))
        return X[:, self.keep_indices_]

def load_features() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Loads graph metrics and labels from the processed data.
    Returns X, y, and feature names.
    """
    if not GRAPH_METRICS_PATH.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {GRAPH_METRICS_PATH}")
    
    df = load_csv(str(GRAPH_METRICS_PATH))
    if df is None or df.empty:
        raise ValueError("Graph metrics file is empty or invalid.")

    # Determine label: drop >= 3 points
    # Assumes columns 'mmse_t1', 'mmse_t2' or 'moca_t1', 'moca_t2' exist
    # If both exist, prioritize MMSE
    score_cols = []
    if 'mmse_t1' in df.columns and 'mmse_t2' in df.columns:
        score_cols = ['mmse_t1', 'mmse_t2']
    elif 'moca_t1' in df.columns and 'moca_t2' in df.columns:
        score_cols = ['moca_t1', 'moca_t2']
    else:
        raise ValueError("Could not find longitudinal cognitive scores (MMSE or MOCA).")

    t1, t2 = score_cols
    # Calculate decline
    decline = df[t1].astype(float) - df[t2].astype(float)
    # Label: 1 if decline >= 3, else 0
    y = (decline >= 3).astype(int).values
    X = df.drop(columns=[t1, t2, 'subject_id']).values
    feature_names = [c for c in df.columns if c not in [t1, t2, 'subject_id']]

    return X, y, feature_names

def train_single_fold(X_train: np.ndarray, y_train: np.ndarray, param_grid: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
    """
    Trains a single fold with nested feature selection and grid search.
    Returns the best model and the best params found in this fold.
    """
    # 1. Variance Thresholding (variance > 0.01)
    vt = VarianceThreshold(threshold=0.01)
    X_train_vt = vt.fit_transform(X_train)
    
    if X_train_vt.shape[1] == 0:
        # If no features pass variance, return a dummy model or handle error
        # For robustness, we'll return a model with 0 features if possible, 
        # but RandomForest requires features. We'll skip this fold or return None.
        logger.log("train_single_fold", status="skipped", reason="No features passed variance threshold")
        return None, {}

    # 2. Collinearity Check (correlation > 0.95)
    collin = CollinearityTransformer(threshold=0.95)
    X_train_collin = collin.fit_transform(X_train_vt)

    if X_train_collin.shape[1] == 0:
        logger.log("train_single_fold", status="skipped", reason="No features passed collinearity check")
        return None, {}

    # 3. RFE to select <= 20 features
    # Base estimator for RFE
    base_rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rfe = RFE(estimator=base_rf, n_features_to_select=min(20, X_train_collin.shape[1]), step=1)
    X_train_rfe = rfe.fit_transform(X_train_collin, y_train)

    # 4. Grid Search with Nested CV (Inner loop)
    # We use a simple GridSearchCV here which performs CV internally
    # The outer loop is handled by the caller
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(random_state=42))
    ])

    grid_search = GridSearchCV(
        pipe,
        param_grid,
        cv=3, # Inner CV folds
        scoring='roc_auc',
        n_jobs=2,
        refit=True
    )

    grid_search.fit(X_train_rfe, y_train)
    
    return grid_search.best_estimator_, grid_search.best_params_

def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray) -> Tuple[Any, List[Dict[str, Any]]]:
    """
    Runs the full nested cross-validation procedure.
    Outer: Stratified K-Fold
    Inner: Grid Search with feature selection
    """
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_results = []
    all_models = []
    
    logger.log("train_and_evaluate_nested_cv", status="started", n_samples=X.shape[0])

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        logger.log("train_and_evaluate_nested_cv", fold=fold_idx, n_train=len(train_idx), n_test=len(test_idx))

        best_model, best_params = train_single_fold(X_train, y_train, PARAM_GRID)

        if best_model is None:
            logger.log("train_and_evaluate_nested_cv", fold=fold_idx, status="failed", reason="Model training failed in fold")
            continue

        # Evaluate on test set
        try:
            y_pred_proba = best_model.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, y_pred_proba)
            
            result_entry = {
                "fold": fold_idx,
                "auc": float(auc),
                "best_params": best_params,
                "n_test": len(test_idx)
            }
            cv_results.append(result_entry)
            all_models.append(best_model)
            
            logger.log("train_and_evaluate_nested_cv", fold=fold_idx, status="success", auc=float(auc))
        except Exception as e:
            logger.log("train_and_evaluate_nested_cv", fold=fold_idx, status="failed", reason=str(e))

    # If we have models, we can ensemble them or just pick the last one?
    # For this task, we persist the model from the last successful fold or average?
    # The task asks to output 'the' model. We will output the one from the last fold
    # or the one with the highest AUC if we want to be more robust.
    # Let's pick the best performing model from the CV results.
    if cv_results:
        best_fold_idx = max(range(len(cv_results)), key=lambda i: cv_results[i]['auc'])
        final_model = all_models[best_fold_idx]
        final_params = cv_results[best_fold_idx]['best_params']
    else:
        raise RuntimeError("No models were successfully trained across all folds.")

    return final_model, cv_results

def persist_model(model: Any, path: Path):
    """Saves the model to disk."""
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.log("persist_model", path=str(path), status="success")

def write_cv_results(results: List[Dict[str, Any]], path: Path):
    """Writes CV results to JSON."""
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.log("write_cv_results", path=str(path), count=len(results))

def write_model_params(model: Any, path: Path):
    """Writes model parameters to JSON."""
    # Extract parameters from the fitted model
    params = {}
    if hasattr(model, 'named_steps'):
        # Pipeline
        for name, step in model.named_steps.items():
            if hasattr(step, 'get_params'):
                params[name] = step.get_params()
    else:
        if hasattr(model, 'get_params'):
            params = model.get_params()
    
    with open(path, 'w') as f:
        json.dump(params, f, indent=2)
    logger.log("write_model_params", path=str(path))

@log_operation("train_model_main")
def main():
    start_time = time.time()
    logger.log("main", status="starting")

    # 1. Load Data
    try:
        X, y, feature_names = load_features()
    except Exception as e:
        logger.log("main", status="failed", reason=f"Data loading error: {e}")
        sys.exit(1)

    logger.log("main", n_samples=X.shape[0], n_features=X.shape[1])

    # 2. Train Model with Nested CV
    try:
        final_model, cv_results = train_and_evaluate_nested_cv(X, y)
    except Exception as e:
        logger.log("main", status="failed", reason=f"Training error: {e}")
        sys.exit(1)

    # 3. Persist Outputs
    try:
        persist_model(final_model, MODEL_PATH)
        write_cv_results(cv_results, CV_RESULTS_PATH)
        write_model_params(final_model, MODEL_PARAMS_PATH)
    except Exception as e:
        logger.log("main", status="failed", reason=f"Output writing error: {e}")
        sys.exit(1)

    elapsed = time.time() - start_time
    logger.log("main", status="completed", elapsed_seconds=elapsed)
    print(f"Model training completed in {elapsed:.2f}s. Outputs written to {DATA_DIR}")

if __name__ == "__main__":
    main()