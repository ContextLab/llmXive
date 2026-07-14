import os
import sys
import json
import time
import warnings
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from joblib import Parallel, delayed
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
from scipy.stats import pearsonr
import joblib

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logger import get_logger
from utils.io import load_csv, save_csv, ensure_dir, save_json
from utils.stats import calculate_correlation_matrix, calculate_feature_variance, filter_low_variance_features

# Constants
DECLINE_THRESHOLD = 3  # Points drop for "decline" label
RANDOM_SEED = 42
MAX_FEATURES = 20
CORRELATION_THRESHOLD = 0.95
VARIANCE_THRESHOLD = 0.01
MEMORY_LIMIT_GB = 7.0
N_JOBS = 2

# Grid search parameters as per spec
PARAM_GRID = {
    'rf__n_estimators': [50, 100, 200],
    'rf__max_depth': [5, 10, None]
}

def get_logger_wrapper(name: str = __name__) -> logging.Logger:
    """Get a logger instance configured for this module."""
    logger = get_logger(name)
    return logger

def define_decline_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    Define the binary decline label based on MMSE/MOCA score drop >= 3 points.
    Assumes columns: 'subject_id', 'score_t1', 'score_t2' (or similar).
    """
    logger = get_logger_wrapper()
    # Determine score columns dynamically or assume standard names
    # Check for common naming conventions
    score_cols = [c for c in df.columns if 'score' in c.lower() or 'mmse' in c.lower() or 'moca' in c.lower()]
    
    if len(score_cols) < 2:
        # Fallback: look for t1/t2 patterns
        t1_cols = [c for c in df.columns if 't1' in c.lower() or 'baseline' in c.lower()]
        t2_cols = [c for c in df.columns if 't2' in c.lower() or 'followup' in c.lower()]
        if len(t1_cols) >= 1 and len(t2_cols) >= 1:
            col_t1 = t1_cols[0]
            col_t2 = t2_cols[0]
        else:
            raise ValueError("Could not identify timepoint score columns for decline calculation.")
    else:
        # Assume first two are the relevant scores
        col_t1 = score_cols[0]
        col_t2 = score_cols[1]

    # Calculate drop
    drop = df[col_t1] - df[col_t2]
    df['decline_label'] = (drop >= DECLINE_THRESHOLD).astype(int)
    
    logger.info(f"Defined decline label: drop >= {DECLINE_THRESHOLD} points between {col_t1} and {col_t2}.")
    logger.info(f"Class distribution: 0 (stable) = {(df['decline_label'] == 0).sum()}, 1 (decline) = {(df['decline_label'] == 1).sum()}")
    
    return df

def collinearity_filter(X: np.ndarray, y: np.ndarray, feature_names: List[str], threshold: float = CORRELATION_THRESHOLD) -> Tuple[np.ndarray, List[str]]:
    """
    Remove features with correlation > threshold. Keep the one with higher variance.
    """
    logger = get_logger_wrapper()
    if X.shape[1] <= 1:
        return X, feature_names

    corr_matrix = calculate_correlation_matrix(X)
    to_drop = set()
    
    # Upper triangle of correlation matrix (excluding diagonal)
    for i in range(X.shape[1]):
        for j in range(i + 1, X.shape[1]):
            if abs(corr_matrix[i, j]) > threshold:
                # Compare variance
                var_i = np.var(X[:, i])
                var_j = np.var(X[:, j])
                if var_i > var_j:
                    to_drop.add(j)
                else:
                    to_drop.add(i)
    
    if to_drop:
        logger.info(f"Collinearity check: Removing {len(to_drop)} highly correlated features (|r| > {threshold}).")
        keep_indices = [i for i in range(X.shape[1]) if i not in to_drop]
        new_feature_names = [feature_names[i] for i in keep_indices]
        return X[:, keep_indices], new_feature_names
    else:
        logger.info("Collinearity check: No highly correlated pairs found.")
        return X, feature_names

def inner_cv_pipeline(X: np.ndarray, y: np.ndarray, param_grid: Dict, n_jobs: int = 2) -> Tuple[Any, Dict]:
    """
    Perform the inner CV loop:
    1. Collinearity check
    2. Variance Thresholding
    3. RFE to select <= MAX_FEATURES
    4. Grid Search CV for Random Forest
    """
    logger = get_logger_wrapper()
    
    # 1. Collinearity Check
    X_clean, feature_names = collinearity_filter(X, y, list(range(X.shape[1])))
    
    # 2. Variance Thresholding
    vt = VarianceThreshold(threshold=VARIANCE_THRESHOLD)
    X_var = vt.fit_transform(X_clean)
    logger.info(f"Variance thresholding: kept {X_var.shape[1]} features (threshold={VARIANCE_THRESHOLD}).")
    
    if X_var.shape[1] == 0:
        raise ValueError("Variance thresholding removed all features.")

    # 3. RFE (Recursive Feature Elimination)
    # Use a simple RF to estimate feature importance for RFE
    rf_base = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=RANDOM_SEED, n_jobs=1)
    rfe = RFE(estimator=rf_base, n_features_to_select=min(MAX_FEATURES, X_var.shape[1]), step=1)
    X_rfe = rfe.fit_transform(X_var)
    logger.info(f"RFE: selected {X_rfe.shape[1]} features.")

    # 4. Grid Search CV
    # Create a pipeline: Scaling -> RF
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=1))
    ])

    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
    
    try:
        grid_search = GridSearchCV(
            pipeline, 
            param_grid, 
            cv=inner_cv, 
            scoring='roc_auc', 
            n_jobs=n_jobs,
            refit=True
        )
        grid_search.fit(X_rfe, y)
        
        best_params = grid_search.best_params_
        logger.info(f"Inner CV Best Parameters: {best_params}")
        
        # Verify FR-003 compliance: n_estimators=100, max_depth=None must be in grid
        if best_params['rf__n_estimators'] == 100 and best_params['rf__max_depth'] is None:
            logger.info("FR-003 Compliance: Best parameters match the base requirement (n=100, max_depth=None).")
        
        return grid_search.best_estimator_, best_params
    except Exception as e:
        logger.error(f"Inner CV Grid Search failed: {e}")
        raise

def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray, outer_splits: int = 5) -> Tuple[List[float], List[float], Dict]:
    """
    Main training loop with Nested Cross-Validation.
    Returns: List of AUCs, List of F1s, and training metadata.
    """
    logger = get_logger_wrapper()
    logger.info(f"Starting Nested CV with {outer_splits} outer folds.")
    
    outer_cv = StratifiedKFold(n_splits=outer_splits, shuffle=True, random_state=RANDOM_SEED)
    auc_scores = []
    f1_scores = []
    best_params_history = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        logger.info(f"Processing outer fold {fold_idx + 1}/{outer_splits}. Train size: {len(y_train)}, Test size: {len(y_test)}")
        
        # Inner CV for this fold
        best_model, best_params = inner_cv_pipeline(X_train, y_train, PARAM_GRID, n_jobs=N_JOBS)
        best_params_history.append(best_params)
        
        # Evaluate on test set
        y_pred_proba = best_model.predict_proba(X_test)[:, 1]
        y_pred = best_model.predict(X_test)
        
        auc = roc_auc_score(y_test, y_pred_proba)
        f1 = f1_score(y_test, y_pred)
        acc = accuracy_score(y_test, y_pred)
        
        auc_scores.append(auc)
        f1_scores.append(f1)
        logger.info(f"Fold {fold_idx + 1}: AUC={auc:.4f}, F1={f1:.4f}, Acc={acc:.4f}")
    
    mean_auc = np.mean(auc_scores)
    std_auc = np.std(auc_scores)
    mean_f1 = np.mean(f1_scores)
    std_f1 = np.std(f1_scores)
    
    logger.info(f"Nested CV Results: AUC={mean_auc:.4f} (+/- {std_auc:.4f}), F1={mean_f1:.4f} (+/- {std_f1:.4f})")
    
    # Aggregate best params (most common or average)
    # For simplicity, we just take the first fold's best params as representative for the final model
    # In a real scenario, we might retrain on full data with these params
    representative_params = best_params_history[0]
    
    return auc_scores, f1_scores, {
        'mean_auc': mean_auc,
        'std_auc': std_auc,
        'mean_f1': mean_f1,
        'std_f1': std_f1,
        'fold_aucs': auc_scores,
        'fold_f1s': f1_scores,
        'best_params': representative_params
    }

def train_final_model(X: np.ndarray, y: np.ndarray, best_params: Dict) -> Any:
    """
    Train the final model on the full dataset using the best parameters found.
    """
    logger = get_logger_wrapper()
    logger.info("Training final model on full dataset.")
    
    # Re-run the feature selection steps on full data to get the final estimator
    # Note: In a strict pipeline, we should fit everything, but for the final output
    # we need a model that can predict on new data.
    # We will replicate the inner pipeline logic without the CV split.
    
    # 1. Collinearity
    X_clean, _ = collinearity_filter(X, y, list(range(X.shape[1])))
    
    # 2. Variance
    vt = VarianceThreshold(threshold=VARIANCE_THRESHOLD)
    X_var = vt.fit_transform(X_clean)
    
    # 3. RFE
    rf_base = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=RANDOM_SEED, n_jobs=1)
    rfe = RFE(estimator=rf_base, n_features_to_select=min(MAX_FEATURES, X_var.shape[1]), step=1)
    X_rfe = rfe.fit_transform(X_var)
    
    # 4. Train Final RF
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(
            n_estimators=best_params.get('rf__n_estimators', 100),
            max_depth=best_params.get('rf__max_depth', None),
            random_state=RANDOM_SEED,
            n_jobs=N_JOBS
        ))
    ])
    
    pipeline.fit(X_rfe, y)
    return pipeline

def main():
    logger = get_logger_wrapper()
    start_time = time.time()
    
    # Paths
    input_path = PROJECT_ROOT / "data" / "processed" / "graph_metrics.csv"
    output_model_path = PROJECT_ROOT / "data" / "processed" / "model.pkl"
    output_report_path = PROJECT_ROOT / "data" / "processed" / "performance_report.json"
    
    if not input_path.exists():
        logger.error(f"Graph metrics file not found: {input_path}")
        logger.error("Please run code/03_compute_graph_metrics.py first.")
        sys.exit(1)
    
    # Load Data
    logger.info(f"Loading graph metrics from {input_path}")
    df = load_csv(input_path)
    
    if df.empty:
        logger.error("Input data is empty.")
        sys.exit(1)
    
    # Define Label
    df = define_decline_label(df)
    
    # Prepare Features and Target
    # Assume all columns except 'subject_id', 'decline_label', and any score columns are features
    exclude_cols = ['subject_id', 'decline_label']
    # Also exclude score columns if they exist (t1, t2 scores)
    score_cols = [c for c in df.columns if 'score' in c.lower() or 'mmse' in c.lower() or 'moca' in c.lower()]
    exclude_cols.extend(score_cols)
    
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    if len(feature_cols) == 0:
        logger.error("No features found for training.")
        sys.exit(1)
    
    X = df[feature_cols].values
    y = df['decline_label'].values
    
    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Target distribution: {np.bincount(y)}")
    
    # Check for class imbalance or insufficient samples
    if len(y) < 10:
        logger.error("Insufficient samples for training.")
        sys.exit(1)
    if len(np.unique(y)) < 2:
        logger.error("Target variable has only one class. Cannot train classifier.")
        sys.exit(1)
    
    # Run Nested CV
    try:
        auc_scores, f1_scores, training_metadata = train_and_evaluate_nested_cv(X, y)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)
    
    # Train Final Model
    best_params = training_metadata['best_params']
    final_model = train_final_model(X, y, best_params)
    
    # Save Model
    ensure_dir(output_model_path)
    joblib.dump(final_model, output_model_path)
    logger.info(f"Final model saved to {output_model_path}")
    
    # Prepare Report
    report = {
        "task_id": "T023",
        "description": "Nested Cross-Validation Training",
        "metrics": {
            "roc_auc_mean": float(training_metadata['mean_auc']),
            "roc_auc_std": float(training_metadata['std_auc']),
            "f1_mean": float(training_metadata['mean_f1']),
            "f1_std": float(training_metadata['std_f1'])
        },
        "fold_results": [
            {"fold": i+1, "auc": float(a), "f1": float(f)} 
            for i, (a, f) in enumerate(zip(training_metadata['fold_aucs'], training_metadata['fold_f1s']))
        ],
        "best_parameters": training_metadata['best_params'],
        "random_seed": RANDOM_SEED,
        "runtime_seconds": time.time() - start_time
    }
    
    # Save Report
    ensure_dir(output_report_path)
    save_json(report, output_report_path)
    logger.info(f"Performance report saved to {output_report_path}")
    
    logger.info("Training completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())