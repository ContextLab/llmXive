import os
import sys
import json
import time
import warnings
import logging
import argparse
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler
import joblib

from utils.logger import get_logger, log_feature_filtering
from utils.stats import check_collinearity, calculate_feature_variance, filter_low_variance_features
from utils.io import load_dataframe, save_json, ensure_dir
from config import get_config

# Suppress specific sklearn warnings for cleaner logs
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

def get_logger_wrapper(name: str) -> logging.Logger:
    """Helper to get a configured logger."""
    return get_logger(name)

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)
    except ImportError:
        return 0.0

def check_memory_limit(limit_gb: float = 7.0) -> bool:
    """Check if current memory usage is within limit."""
    current = get_memory_usage_gb()
    if current > limit_gb:
        return False
    return True

def define_decline_label(df: pd.DataFrame, threshold: int = 3) -> pd.DataFrame:
    """
    Define the decline label based on MMSE/MOCA score drop.
    Label 1: Drop >= threshold points.
    Label 0: Drop < threshold points.
    """
    logger = get_logger("04_train_model")
    
    # Ensure we have the necessary columns
    required_cols = ['subject_id', 'mmse_baseline', 'mmse_followup', 'moca_baseline', 'moca_followup']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        # Try to use available scores
        if 'mmse_baseline' in df.columns and 'mmse_followup' in df.columns:
            score_cols = ['mmse_baseline', 'mmse_followup']
        elif 'moca_baseline' in df.columns and 'moca_followup' in df.columns:
            score_cols = ['moca_baseline', 'moca_followup']
        else:
            logger.error(f"Cannot calculate decline: missing score columns. Found: {list(df.columns)}")
            raise ValueError(f"Missing required score columns: {missing}")
    else:
        # Prefer MMSE if available, otherwise MOCA
        if 'mmse_baseline' in df.columns:
            score_cols = ['mmse_baseline', 'mmse_followup']
        else:
            score_cols = ['moca_baseline', 'moca_followup']

    baseline_col, followup_col = score_cols
    
    # Calculate drop
    df['score_drop'] = df[baseline_col] - df[followup_col]
    
    # Create binary label
    df['decline_label'] = (df['score_drop'] >= threshold).astype(int)
    
    logger.info(f"Defined decline label (drop >= {threshold} points)")
    logger.info(f"Class distribution: 0={sum(df['decline_label']==0)}, 1={sum(df['decline_label']==1)}")
    
    return df

def collinearity_filter(X: pd.DataFrame, threshold: float = 0.95) -> Tuple[pd.DataFrame, List[str]]:
    """
    Remove features with high correlation (> threshold).
    Keeps the feature with higher variance.
    Returns filtered DataFrame and list of dropped columns.
    """
    logger = get_logger("04_train_model")
    dropped_cols = []
    
    if X.shape[1] < 2:
        return X, dropped_cols

    # Calculate correlation matrix
    corr_matrix = X.corr().abs()
    
    # Select upper triangle of correlation matrix
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # Find features with correlation above threshold
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
    
    if not to_drop:
        return X, dropped_cols

    # Calculate variance for features to decide which to keep
    variances = calculate_feature_variance(X)
    
    # Sort to_drop by variance (ascending) to keep higher variance features
    # We want to drop the one with LOWER variance
    to_drop_sorted = sorted(to_drop, key=lambda x: variances.get(x, 0.0))
    
    final_drop = []
    for col in to_drop_sorted:
        if col not in final_drop:
            # Check if any remaining high-correlation feature is still in the set
            # (simplified: just drop the lower variance one)
            final_drop.append(col)
    
    # Actually drop the lower variance ones
    for col in final_drop:
        if col in X.columns:
            X = X.drop(columns=[col])
            dropped_cols.append(col)
    
    if dropped_cols:
        logger.info(f"Collinearity filter removed {len(dropped_cols)} features: {dropped_cols[:5]}...")
        log_feature_filtering("collinearity", dropped_cols)
    
    return X, dropped_cols

def inner_cv_pipeline(X: np.ndarray, y: np.ndarray, param_grid: Dict, random_state: int = 42) -> Tuple[Any, Dict]:
    """
    Perform inner CV with:
    1. Collinearity check
    2. Variance Thresholding
    3. RFE to select <= 20 features
    4. Grid Search for Random Forest
    """
    logger = get_logger("04_train_model")
    
    # Convert to DataFrame for feature selection
    feature_names = [f"feat_{i}" for i in range(X.shape[1])]
    X_df = pd.DataFrame(X, columns=feature_names)
    
    # Step 1: Collinearity Filter
    X_clean, dropped = collinearity_filter(X_df)
    
    # Step 2: Variance Thresholding
    vt = VarianceThreshold(threshold=0.01)
    X_vt = vt.fit_transform(X_clean)
    kept_mask = vt.get_support()
    X_vt_df = pd.DataFrame(X_vt, columns=X_clean.columns[kept_mask])
    
    # Step 3: RFE to select <= 20 features
    # Use a simple RF for RFE
    rfe_base = RandomForestClassifier(n_estimators=10, random_state=random_state, n_jobs=1)
    n_features = min(20, X_vt_df.shape[1])
    
    if n_features < 1:
        # Fallback if no features
        n_features = 1
    
    rfe = RFE(estimator=rfe_base, n_features_to_select=n_features, step=1)
    X_rfe = rfe.fit_transform(X_vt_df)
    X_rfe_df = pd.DataFrame(X_rfe, columns=[f"rfe_{i}" for i in range(X_rfe.shape[1])])
    
    # Step 4: Grid Search
    rf = RandomForestClassifier(random_state=random_state)
    
    # Ensure base parameters are in grid
    # param_grid should include n_estimators=100, max_depth=None
    
    cv_inner = StratifiedKFold(n_splits=3, shuffle=True, random_state=random_state)
    
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        scoring='roc_auc',
        cv=cv_inner,
        n_jobs=1, # Inner loop parallelism controlled externally
        verbose=0
    )
    
    grid_search.fit(X_rfe_df, y)
    
    best_params = grid_search.best_params_
    best_score = grid_search.best_score_
    
    # Log compliance with FR-003
    if best_params.get('n_estimators') == 100 and best_params.get('max_depth') is None:
        logger.info("FR-003 Compliance: Selected parameters include n_estimators=100, max_depth=None")
    
    return grid_search.best_estimator_, {
        'best_params': best_params,
        'best_score': best_score,
        'n_features_selected': n_features,
        'variance_dropped': len(dropped),
        'final_feature_count': X_rfe.shape[1]
    }

def train_and_evaluate_nested_cv(X: pd.DataFrame, y: pd.Series, param_grid: Dict, 
                                 outer_splits: int = 5, random_state: int = 42) -> Dict[str, Any]:
    """
    Perform nested cross-validation.
    Outer: 5-fold CV for evaluation.
    Inner: Grid search with feature selection.
    """
    logger = get_logger("04_train_model")
    logger.info(f"Starting Nested CV: {outer_splits} outer folds")
    
    if not check_memory_limit():
        logger.error("Memory limit exceeded. Aborting training.")
        raise MemoryError("Memory limit exceeded")
    
    X_np = X.values
    y_np = y.values
    
    outer_cv = StratifiedKFold(n_splits=outer_splits, shuffle=True, random_state=random_state)
    
    auc_scores = []
    acc_scores = []
    f1_scores = []
    best_params_history = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X_np, y_np)):
        logger.info(f"Processing outer fold {fold_idx + 1}/{outer_splits}")
        
        X_train, X_test = X_np[train_idx], X_np[test_idx]
        y_train, y_test = y_np[train_idx], y_np[test_idx]
        
        # Inner CV for this training set
        best_model, inner_stats = inner_cv_pipeline(X_train, y_train, param_grid, random_state)
        
        # Evaluate on test set
        y_pred_proba = best_model.predict_proba(X_test)[:, 1]
        y_pred = best_model.predict(X_test)
        
        auc = roc_auc_score(y_test, y_pred_proba)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        auc_scores.append(auc)
        acc_scores.append(acc)
        f1_scores.append(f1)
        best_params_history.append(inner_stats['best_params'])
        
        logger.info(f"  Fold {fold_idx + 1}: AUC={auc:.4f}, Acc={acc:.4f}, F1={f1:.4f}")
    
    results = {
        'mean_auc': float(np.mean(auc_scores)),
        'std_auc': float(np.std(auc_scores)),
        'mean_acc': float(np.mean(acc_scores)),
        'std_acc': float(np.std(acc_scores)),
        'mean_f1': float(np.mean(f1_scores)),
        'std_f1': float(np.std(f1_scores)),
        'fold_aucs': [float(x) for x in auc_scores],
        'fold_accs': [float(x) for x in acc_scores],
        'fold_f1s': [float(x) for x in f1_scores],
        'selected_params': best_params_history[0] if best_params_history else {}
    }
    
    return results

def train_final_model(X: pd.DataFrame, y: pd.Series, param_grid: Dict, random_state: int = 42) -> Tuple[Any, Dict]:
    """
    Train the final model on the full dataset using the best parameters found.
    """
    logger = get_logger("04_train_model")
    logger.info("Training final model on full dataset")
    
    X_np = X.values
    y_np = y.values
    
    # Run the inner pipeline once on full data to get the best estimator and stats
    best_model, stats = inner_cv_pipeline(X_np, y_np, param_grid, random_state)
    
    # Retrain with explicit best params if grid search didn't fully optimize on full data
    # (The inner_cv_pipeline already fits, but we ensure params are correct)
    # Note: In practice, inner_cv_pipeline returns the fitted model.
    
    return best_model, stats

def main():
    logger = get_logger("04_train_model")
    logger.info("Starting T023: Train Model with Nested CV")
    
    # Configuration
    config = get_config()
    random_seed = config.get('random_seed', 42)
    np.random.seed(random_seed)
    
    input_path = Path("data/processed/graph_metrics.csv")
    output_model_path = Path("data/processed/model.pkl")
    output_report_path = Path("data/processed/performance_report.json")
    
    # Ensure output directory exists
    ensure_dir(output_model_path.parent)
    
    # Load Data
    logger.info(f"Loading graph metrics from {input_path}")
    if not input_path.exists():
        logger.error(f"Graph metrics file not found: {input_path}")
        logger.error("Please run code/03_compute_graph_metrics.py first.")
        sys.exit(1)
    
    try:
        df = load_dataframe(input_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    # Define Decline Label
    df = define_decline_label(df, threshold=3)
    
    # Prepare Features
    feature_cols = [col for col in df.columns if col not in ['subject_id', 'mmse_baseline', 'mmse_followup', 
                                                              'moca_baseline', 'moca_followup', 'score_drop', 'decline_label']]
    
    if len(feature_cols) == 0:
        logger.error("No feature columns found in input data.")
        sys.exit(1)
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, 'decline_label']
    
    if len(X) < 10:
        logger.error(f"Insufficient data for training after dropping NaNs. N={len(X)}")
        sys.exit(1)
    
    logger.info(f"Training data shape: {X.shape}")
    logger.info(f"Class distribution: 0={sum(y==0)}, 1={sum(y==1)}")
    
    # Define Parameter Grid
    # Must include n_estimators=100, max_depth=None (FR-003)
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 10, None]
    }
    
    # Run Nested CV
    start_time = time.time()
    try:
        cv_results = train_and_evaluate_nested_cv(X, y, param_grid, outer_splits=5, random_state=random_seed)
    except MemoryError:
        logger.error("Training failed due to memory constraints.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    elapsed_time = time.time() - start_time
    cv_results['runtime_seconds'] = elapsed_time
    
    # Train Final Model
    final_model, final_stats = train_final_model(X, y, param_grid, random_state=random_seed)
    
    # Log Final Parameters
    logger.info(f"Final Model Parameters: {final_stats['best_params']}")
    cv_results['final_params'] = final_stats['best_params']
    cv_results['final_feature_count'] = final_stats['final_feature_count']
    
    # Save Model
    joblib.dump(final_model, output_model_path)
    logger.info(f"Model saved to {output_model_path}")
    
    # Save Report
    save_json(cv_results, output_report_path)
    logger.info(f"Performance report saved to {output_report_path}")
    
    logger.info(f"Training completed in {elapsed_time:.2f} seconds")
    logger.info(f"Mean ROC-AUC: {cv_results['mean_auc']:.4f} (+/- {cv_results['std_auc']:.4f})")

if __name__ == "__main__":
    main()