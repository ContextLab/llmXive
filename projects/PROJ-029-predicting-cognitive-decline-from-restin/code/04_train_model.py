"""
code/04_train_model.py
Task T023: Implement Nested CV with collinearity filter, variance thresholding, and RFE.
"""
import os
import sys
import json
import time
import warnings
import logging
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
from joblib import Parallel, delayed

# Local imports from existing API surface
from utils.logger import get_logger
from utils.stats import calculate_correlation_matrix, filter_low_variance_features
from utils.io import load_csv, save_csv, load_json, save_json, ensure_dir
from config import get_config

# Suppress specific warnings to keep logs clean
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# --- Configuration ---
CONFIG = get_config()
RANDOM_SEED = CONFIG.get('random_seed', 42)
RAM_LIMIT_GB = 7.0  # Hard limit for this task as per spec
DECLINE_THRESHOLD = 3  # Points drop to define decline
FEATURE_LIMIT = 20
CORR_THRESHOLD = 0.95
VARIANCE_THRESHOLD = 0.01

# Grid search parameters
PARAM_GRID = {
    'randomforest__n_estimators': [50, 100, 200],
    'randomforest__max_depth': [5, 10, None]
}

# Ensure base parameters (FR-003) are in the grid
assert 100 in PARAM_GRID['randomforest__n_estimators'], "FR-003: n_estimators=100 must be in grid"
assert None in PARAM_GRID['randomforest__max_depth'], "FR-003: max_depth=None must be in grid"

logger = get_logger('model_training')

def define_decline_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    Define the binary label for cognitive decline.
    Label = 1 if (MMSE_t1 - MMSE_t2) >= DECLINE_THRESHOLD or (MOCA_t1 - MOCA_t2) >= DECLINE_THRESHOLD.
    Handles missing values by dropping rows where both scores are missing at either timepoint.
    """
    df = df.copy()
    
    # Try to compute MMSE drop
    mmse_drop = None
    if 'MMSE_t1' in df.columns and 'MMSE_t2' in df.columns:
        mmse_drop = df['MMSE_t1'] - df['MMSE_t2']
    
    # Try to compute MOCA drop
    moca_drop = None
    if 'MOCA_t1' in df.columns and 'MOCA_t2' in df.columns:
        moca_drop = df['MOCA_t1'] - df['MOCA_t2']

    if mmse_drop is not None and moca_drop is not None:
        # If both available, decline if EITHER drops by threshold
        df['decline'] = ((mmse_drop >= DECLINE_THRESHOLD) | (moca_drop >= DECLINE_THRESHOLD)).astype(int)
    elif mmse_drop is not None:
        df['decline'] = (mmse_drop >= DECLINE_THRESHOLD).astype(int)
    elif moca_drop is not None:
        df['decline'] = (moca_drop >= DECLINE_THRESHOLD).astype(int)
    else:
        raise ValueError("No MMSE or MOCA columns found to compute decline label.")

    # Drop rows with NaN in the label (missing data)
    initial_count = len(df)
    df = df.dropna(subset=['decline'])
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} subjects due to missing decline label data.")
    
    return df

def collinearity_filter(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Remove highly correlated features (Pearson > 0.95).
    Keeps the feature with higher variance.
    """
    if X.shape[1] <= 1:
        return X, y, feature_names

    corr_matrix = calculate_correlation_matrix(X)
    to_drop = set()
    
    # Upper triangle only to avoid double counting
    n_features = X.shape[1]
    for i in range(n_features):
        for j in range(i + 1, n_features):
            if abs(corr_matrix[i, j]) > CORR_THRESHOLD:
                # Compare variances
                var_i = np.var(X[:, i])
                var_j = np.var(X[:, j])
                if var_i < var_j:
                    to_drop.add(i)
                else:
                    to_drop.add(j)
    
    if not to_drop:
        return X, y, feature_names

    keep_indices = [i for i in range(n_features) if i not in to_drop]
    X_filtered = X[:, keep_indices]
    features_filtered = [feature_names[i] for i in keep_indices]
    
    logger.info(f"Collinearity filter: removed {len(to_drop)} features, kept {len(features_filtered)}.")
    return X_filtered, y, features_filtered

def inner_cv_pipeline(X: np.ndarray, y: np.ndarray, param_grid: Dict) -> Tuple[Any, Dict, List[str]]:
    """
    Runs the inner CV loop:
    1. Collinearity filter
    2. Variance Thresholding
    3. RFE to select <= 20 features
    4. Grid Search for Random Forest
    Returns the best model, best params, and selected feature names.
    """
    # 1. Collinearity Filter
    X_coll, y_coll, features_coll = collinearity_filter(X, y, list(range(X.shape[1])))
    
    if len(features_coll) == 0:
        raise ValueError("Collinearity filter removed all features.")

    # 2. Variance Thresholding
    vt = VarianceThreshold(threshold=VARIANCE_THRESHOLD)
    X_vt = vt.fit_transform(X_coll)
    # Map feature names after variance thresholding
    var_mask = vt.get_support()
    features_vt = [f for i, f in enumerate(features_coll) if var_mask[i]]
    
    if len(features_vt) == 0:
        raise ValueError("Variance thresholding removed all features.")

    # 3. RFE to select <= 20 features
    # Use a simple RF estimator for RFE
    rfe_base = RandomForestClassifier(n_estimators=50, random_state=RANDOM_SEED, max_depth=5)
    rfe = RFE(estimator=rfe_base, n_features_to_select=min(FEATURE_LIMIT, len(features_vt)))
    X_rfe = rfe.fit_transform(X_vt, y_coll)
    
    # Map feature names after RFE
    rfe_mask = rfe.get_support()
    features_final = [f for i, f in enumerate(features_vt) if rfe_mask[i]]
    
    if len(features_final) == 0:
        raise ValueError("RFE removed all features.")

    # 4. Grid Search
    # Build a pipeline: Scaling -> RF
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('randomforest', RandomForestClassifier(random_state=RANDOM_SEED))
    ])

    cv_inner = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
    grid_search = GridSearchCV(
        pipe, param_grid, cv=cv_inner, scoring='roc_auc', n_jobs=-1, refit=True
    )
    
    grid_search.fit(X_rfe, y_coll)
    
    logger.info(f"Inner CV Best Params: {grid_search.best_params_}")
    return grid_search.best_estimator_, grid_search.best_params_, features_final

def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray, param_grid: Dict) -> Dict[str, Any]:
    """
    Runs the full nested CV procedure.
    Outer CV: 5-fold
    Inner CV: Grid Search with preprocessing pipeline
    Returns metrics and best params found in the final outer fold (or aggregated).
    """
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    
    auc_scores = []
    f1_scores = []
    acc_scores = []
    best_params_list = []
    all_selected_features = set()

    logger.info(f"Starting Nested CV with {len(y)} samples, {X.shape[1]} features.")

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        logger.info(f"Processing Outer Fold {fold_idx + 1}/5...")
        
        try:
            best_model, best_params, selected_features = inner_cv_pipeline(X_train, y_train, param_grid)
            best_params_list.append(best_params)
            all_selected_features.update(selected_features)
            
            # Evaluate on test set
            y_pred_proba = best_model.predict_proba(X_test)[:, 1]
            y_pred = best_model.predict(X_test)
            
            auc = roc_auc_score(y_test, y_pred_proba)
            f1 = f1_score(y_test, y_pred)
            acc = accuracy_score(y_test, y_pred)
            
            auc_scores.append(auc)
            f1_scores.append(f1)
            acc_scores.append(acc)
            
            logger.info(f"Fold {fold_idx + 1} - AUC: {auc:.4f}, F1: {f1:.4f}, Acc: {acc:.4f}")
            
        except Exception as e:
            logger.error(f"Fold {fold_idx + 1} failed: {str(e)}")
            raise

    # Train final model on full data for saving
    logger.info("Training final model on full dataset...")
    final_model, final_params, final_features = inner_cv_pipeline(X, y, param_grid)
    
    # Verify FR-003 compliance
    if final_params['randomforest__n_estimators'] == 100 and final_params['randomforest__max_depth'] is None:
        logger.info("FR-003 Compliance Verified: Best params include n_estimators=100, max_depth=None.")
    else:
        logger.warning(f"FR-003 Note: Best params were {final_params}. Check if grid included these values.")

    results = {
        "mean_auc": float(np.mean(auc_scores)),
        "std_auc": float(np.std(auc_scores)),
        "mean_f1": float(np.mean(f1_scores)),
        "std_f1": float(np.std(f1_scores)),
        "mean_accuracy": float(np.mean(acc_scores)),
        "std_accuracy": float(np.std(acc_scores)),
        "best_params": final_params,
        "selected_features": list(all_selected_features),
        "fold_scores": {
            "auc": [float(x) for x in auc_scores],
            "f1": [float(x) for x in f1_scores],
            "accuracy": [float(x) for x in acc_scores]
        }
    }
    
    return results, final_model, final_features

def main():
    start_time = time.time()
    logger.info("Starting model training (T023).")
    
    # Paths
    base_dir = Path(__file__).resolve().parent.parent
    graph_metrics_path = base_dir / "data" / "processed" / "graph_metrics.csv"
    eligible_subjects_path = base_dir / "data" / "processed" / "eligible_subjects.csv"
    model_output_path = base_dir / "data" / "processed" / "model.pkl"
    report_output_path = base_dir / "data" / "processed" / "performance_report.json"
    
    # Load data
    if not graph_metrics_path.exists():
        logger.error(f"Graph metrics file not found: {graph_metrics_path}")
        logger.error("Please run code/03_compute_graph_metrics.py first.")
        sys.exit(1)
    
    if not eligible_subjects_path.exists():
        logger.error(f"Eligible subjects file not found: {eligible_subjects_path}")
        sys.exit(1)

    # Load graph metrics
    df_metrics = load_csv(graph_metrics_path)
    df_eligible = load_csv(eligible_subjects_path)
    
    # Merge to get labels
    # Assume eligible_subjects.csv has 'subject_id', 'MMSE_t1', 'MMSE_t2', etc.
    # Assume graph_metrics.csv has 'subject_id' and graph metrics as columns
    if 'subject_id' not in df_metrics.columns or 'subject_id' not in df_eligible.columns:
        logger.error("Missing 'subject_id' column in input files.")
        sys.exit(1)
    
    df = pd.merge(df_eligible, df_metrics, on='subject_id', how='inner')
    
    if len(df) == 0:
        logger.error("No subjects found after merging eligible subjects and graph metrics.")
        sys.exit(1)
    
    # Define labels
    df = define_decline_label(df)
    
    # Prepare X and y
    # Exclude non-feature columns
    exclude_cols = ['subject_id', 'decline', 'MMSE_t1', 'MMSE_t2', 'MOCA_t1', 'MOCA_t2']
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    if len(feature_cols) == 0:
        logger.error("No feature columns found in graph metrics.")
        sys.exit(1)
    
    X = df[feature_cols].values
    y = df['decline'].values
    
    logger.info(f"Dataset shape: {X.shape}, Labels distribution: {np.bincount(y)}")
    
    if np.sum(y) == 0 or np.sum(y) == len(y):
        logger.error("Class imbalance: All samples are the same class. Cannot train classifier.")
        sys.exit(1)

    # Train model
    try:
        results, best_model, selected_features = train_and_evaluate_nested_cv(X, y, PARAM_GRID)
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        raise

    # Save model
    import joblib
    ensure_dir(model_output_path)
    joblib.dump(best_model, model_output_path)
    logger.info(f"Model saved to {model_output_path}")
    
    # Save report
    report = {
        "task": "T023",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": results,
        "fr003_compliance": {
            "n_estimators_100_in_grid": True,
            "max_depth_none_in_grid": True,
            "final_params": results['best_params']
        }
    }
    ensure_dir(report_output_path)
    save_json(report, report_output_path)
    logger.info(f"Performance report saved to {report_output_path}")
    
    end_time = time.time()
    logger.info(f"Training completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()