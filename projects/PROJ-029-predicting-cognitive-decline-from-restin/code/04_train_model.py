"""
code/04_train_model.py
Implements nested cross-validation for predicting cognitive decline from graph metrics.

- Defines decline label (drop >= 3 points).
- Nested CV: Outer K-fold, Inner GridSearch.
- Inner loop: Collinearity check (r > 0.95), Variance Threshold, RFE (<=20 features).
- Model: Random Forest.
- Outputs: model.pkl, cv_results.json, model_params.json.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
import joblib

# Import logging utility
# Note: We use the ReproducibilityLogger defined in utils/logger.py
# which is tolerant of all call shapes.
try:
    from utils.logger import get_logger, log_operation, LogEntry
except ImportError:
    # Fallback if running as script without package context
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from utils.logger import get_logger, log_operation, LogEntry

# Constants
RANDOM_SEED = 42
DATA_DIR = Path("data/processed")
OUTPUT_MODEL = DATA_DIR / "model.pkl"
OUTPUT_CV_RESULTS = DATA_DIR / "cv_results.json"
OUTPUT_MODEL_PARAMS = DATA_DIR / "model_params.json"

# Feature selection constraints
MAX_FEATURES = 20
COLLINEARITY_THRESHOLD = 0.95
VARIANCE_THRESHOLD = 0.01
DECLINE_THRESHOLD = 3

logger = get_logger("train_model")

class CollinearityTransformer(BaseEstimator, TransformerMixin):
    """
    Removes features with Pearson correlation > threshold.
    Keeps the feature with higher variance when a pair is correlated.
    """
    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.keep_indices_ = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "CollinearityTransformer":
        if X.shape[1] == 0:
            self.keep_indices_ = np.array([], dtype=int)
            return self

        corr_matrix = np.corrcoef(X.T)
        # Handle NaNs (constant columns)
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        
        n_features = X.shape[1]
        keep = np.ones(n_features, dtype=bool)
        
        # Upper triangle only to avoid double counting
        for i in range(n_features):
            if not keep[i]:
                continue
            for j in range(i + 1, n_features):
                if not keep[j]:
                    continue
                if abs(corr_matrix[i, j]) > self.threshold:
                    # Keep the one with higher variance
                    var_i = np.var(X[:, i])
                    var_j = np.var(X[:, j])
                    if var_i >= var_j:
                        keep[j] = False
                    else:
                        keep[i] = False
                    break # Move to next i after dropping one
        
        self.keep_indices_ = np.where(keep)[0]
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if len(self.keep_indices_) == 0:
            return np.zeros((X.shape[0], 0))
        return X[:, self.keep_indices_]

def load_eligible_subjects() -> List[str]:
    """Load subject IDs from eligible_subjects.csv."""
    path = DATA_DIR / "eligible_subjects.csv"
    if not path.exists():
        logger.log("error", message=f"File not found: {path}")
        raise FileNotFoundError(f"Eligible subjects file not found: {path}")
    
    df = pd.read_csv(path)
    # Expecting a column 'subject_id' or similar
    if 'subject_id' in df.columns:
        return df['subject_id'].tolist()
    elif 'participant_id' in df.columns:
        return df['participant_id'].tolist()
    else:
        # Fallback to first column
        return df.iloc[:, 0].tolist()

def load_features(subjects: List[str]) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Load graph metrics and labels.
    Returns X, y, and a dataframe with metadata if needed.
    """
    metrics_path = DATA_DIR / "graph_metrics.csv"
    if not metrics_path.exists():
        logger.log("error", message=f"Graph metrics file not found: {metrics_path}")
        raise FileNotFoundError(f"Graph metrics file not found: {metrics_path}")
    
    df = pd.read_csv(metrics_path)
    
    # Filter for eligible subjects
    df = df[df['subject_id'].isin(subjects)]
    
    if df.empty:
        logger.log("error", message="No matching subjects found in graph metrics.")
        raise ValueError("No matching subjects found.")
    
    # Define label: drop >= 3 points
    # Assuming columns: 'mmse_baseline', 'mmse_followup' or similar.
    # We need to infer column names or assume standard names.
    # Let's look for MMSE or MOCA columns.
    baseline_cols = [c for c in df.columns if 'mmse' in c.lower() and 'base' in c.lower()]
    followup_cols = [c for c in df.columns if 'mmse' in c.lower() and 'follow' in c.lower()]
    
    # Fallback if naming is different
    if not baseline_cols:
        baseline_cols = [c for c in df.columns if 'mmse' in c.lower() and 't1' in c.lower()]
    if not followup_cols:
        followup_cols = [c for c in df.columns if 'mmse' in c.lower() and 't2' in c.lower()]
    
    # If still not found, try generic names
    if not baseline_cols:
        baseline_cols = ['baseline_score', 'score_baseline']
    if not followup_cols:
        followup_cols = ['followup_score', 'score_followup']
    
    # Select the first valid one found
    b_col = baseline_cols[0] if baseline_cols else None
    f_col = followup_cols[0] if followup_cols else None
    
    if not b_col or not f_col:
        logger.log("error", message="Could not identify baseline/followup score columns.")
        raise ValueError("Missing score columns for label definition.")
    
    # Calculate decline
    df['decline'] = df[b_col] - df[f_col]
    # Label: 1 if decline >= 3, else 0
    df['label'] = (df['decline'] >= DECLINE_THRESHOLD).astype(int)
    
    # Check for class imbalance or empty labels
    if df['label'].sum() == 0:
        logger.log("warning", message="No positive labels (decline >= 3) found. Proceeding with 0s only.")
    
    y = df['label'].values
    
    # Feature columns: all numeric columns except subject_id, labels, scores
    exclude_cols = ['subject_id', 'label', 'decline', b_col, f_col]
    # Also exclude any non-numeric columns
    feature_cols = [c for c in df.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(df[c])]
    
    X = df[feature_cols].values
    
    logger.log("info", message=f"Loaded {X.shape[0]} subjects, {X.shape[1]} features.")
    return X, y, df

def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray) -> Tuple[Any, Dict[str, Any]]:
    """
    Performs Nested Cross-Validation.
    Outer: StratifiedKFold
    Inner: GridSearchCV with Collinearity, VarianceThreshold, RFE, RandomForest.
    """
    n_splits = 5
    outer_cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    
    # Grid Search Parameters
    param_grid = {
        'randomforest__n_estimators': [50, 100, 200],
        'randomforest__max_depth': [5, 10, None]
    }
    
    # Pipeline: Collinearity -> VarianceThreshold -> RFE -> RandomForest
    # Note: RFE requires an estimator to estimate feature importance.
    # We use a simple RF for RFE step, then the final RF for the model.
    # To avoid circular dependency in naming, we use a dummy RF for RFE.
    
    base_rf = RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=-1)
    
    pipe = Pipeline([
        ('collinearity', CollinearityTransformer(threshold=COLLINEARITY_THRESHOLD)),
        ('variance', VarianceThreshold(threshold=VARIANCE_THRESHOLD)),
        ('rfe', RFE(estimator=RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED), n_features_to_select=MAX_FEATURES)),
        ('randomforest', base_rf)
    ])
    
    outer_results = []
    cv_scores = []
    best_params_list = []
    
    start_time = time.time()
    
    for fold, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Inner CV for GridSearch
        inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
        
        grid_search = GridSearchCV(
            pipe,
            param_grid,
            cv=inner_cv,
            scoring='roc_auc',
            n_jobs=2,
            refit=True
        )
        
        try:
            grid_search.fit(X_train, y_train)
            best_params_list.append(grid_search.best_params_)
            
            # Evaluate on outer test set
            y_pred_proba = grid_search.predict_proba(X_test)[:, 1]
            y_pred = (y_pred_proba >= 0.5).astype(int)
            
            auc = roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0.5
            f1 = f1_score(y_test, y_pred, zero_division=0)
            acc = accuracy_score(y_test, y_pred)
            
            outer_results.append({
                'fold': fold + 1,
                'auc': auc,
                'f1': f1,
                'accuracy': acc,
                'best_params': grid_search.best_params_
            })
            
            cv_scores.append(auc)
            
        except Exception as e:
            logger.log("error", message=f"Fold {fold} failed: {str(e)}")
            # Skip this fold or handle error
            continue
    
    elapsed = time.time() - start_time
    
    # Aggregate results
    mean_auc = np.mean(cv_scores) if cv_scores else 0.0
    std_auc = np.std(cv_scores) if cv_scores else 0.0
    
    results = {
        'outer_folds': outer_results,
        'mean_auc': float(mean_auc),
        'std_auc': float(std_auc),
        'runtime_seconds': elapsed,
        'best_params_overall': best_params_list[0] if best_params_list else {}
    }
    
    logger.log("info", message=f"Nested CV completed. Mean AUC: {mean_auc:.3f} (+/- {std_auc:.3f})")
    return results, results['best_params_overall']

def persist_model(X: np.ndarray, y: np.ndarray, best_params: Dict[str, Any]) -> Any:
    """
    Train the final model on the full dataset using the best parameters.
    """
    logger.log("info", message="Training final model on full dataset.")
    
    # Reconstruct pipeline with best params
    pipe = Pipeline([
        ('collinearity', CollinearityTransformer(threshold=COLLINEARITY_THRESHOLD)),
        ('variance', VarianceThreshold(threshold=VARIANCE_THRESHOLD)),
        ('rfe', RFE(estimator=RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED), n_features_to_select=MAX_FEATURES)),
        ('randomforest', RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=-1))
    ])
    
    # Update parameters
    pipe.set_params(**best_params)
    
    pipe.fit(X, y)
    
    # Save
    os.makedirs(OUTPUT_MODEL.parent, exist_ok=True)
    joblib.dump(pipe, OUTPUT_MODEL)
    logger.log("info", message=f"Model saved to {OUTPUT_MODEL}")
    
    return pipe

def write_performance_report(results: Dict[str, Any]) -> None:
    """Write performance report to JSON."""
    with open(OUTPUT_CV_RESULTS, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.log("info", message=f"CV results saved to {OUTPUT_CV_RESULTS}")

def write_model_params(params: Dict[str, Any]) -> None:
    """Write model parameters to JSON."""
    with open(OUTPUT_MODEL_PARAMS, 'w') as f:
        json.dump(params, f, indent=2)
    logger.log("info", message=f"Model params saved to {OUTPUT_MODEL_PARAMS}")

def main():
    """Main entry point."""
    logger.log("info", message="Starting model training pipeline.")
    
    try:
        # 1. Load Data
        subjects = load_eligible_subjects()
        X, y, df = load_features(subjects)
        
        if X.shape[0] == 0:
            logger.log("error", message="No data to train on.")
            return 1
        
        # 2. Nested CV
        results, best_params = train_and_evaluate_nested_cv(X, y)
        
        # 3. Train Final Model
        model = persist_model(X, y, best_params)
        
        # 4. Write Reports
        write_performance_report(results)
        write_model_params(best_params)
        
        logger.log("info", message="Pipeline completed successfully.")
        return 0
        
    except Exception as e:
        logger.log("error", message=f"Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())