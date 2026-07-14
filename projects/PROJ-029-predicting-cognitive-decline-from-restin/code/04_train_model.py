"""
T023: Train Model with Nested Cross-Validation
Implements nested CV with collinearity check, variance thresholding, and RFE.
"""
import os
import sys
import json
import time
import warnings
import logging
import random
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold, RFE
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr
import joblib

# Import project utilities
from utils.logger import get_logger
from utils.io import load_csv, save_json, ensure_dir
from utils.stats import check_collinearity, calculate_feature_variance, filter_low_variance_features
from config import get_config

# Configuration
RANDOM_SEED = 42
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"

GRAPH_METRICS_PATH = DATA_DIR / "graph_metrics.csv"
MODEL_OUTPUT_PATH = DATA_DIR / "model.pkl"
PERFORMANCE_REPORT_PATH = DATA_DIR / "performance_report.json"
LOGS_DIR = DATA_DIR / "logs"

# Ensure directories exist
ensure_dir(LOGS_DIR)
ensure_dir(DATA_DIR)
ensure_dir(ARTIFACTS_DIR)

logger = get_logger("04_train_model", LOGS_DIR / "training.log")

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)
    except Exception as e:
        logger.warning(f"Could not get memory usage: {e}")
        return 0.0

def check_memory_limit(limit_gb: float = 7.0) -> bool:
    """Check if memory usage is within limit."""
    current = get_memory_usage_gb()
    if current > limit_gb:
        logger.error(f"Memory usage {current:.2f}GB exceeds limit {limit_gb}GB")
        return False
    return True

def define_decline_label(df: pd.DataFrame, threshold: int = 3) -> pd.DataFrame:
    """
    Define cognitive decline label.
    Decline = (Score_T1 - Score_T0) >= threshold
    """
    # Ensure we have the required columns
    required_cols = ['subject_id', 'mmse_t0', 'mmse_t1']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        # Try alternative columns (e.g., moca)
        if 'moca_t0' in df.columns and 'moca_t1' in df.columns:
            logger.info("Using MOC scores instead of MMSE")
            score_t0 = df['moca_t0']
            score_t1 = df['moca_t1']
        else:
            raise ValueError(f"Missing required score columns. Found: {df.columns.tolist()}, Required: {required_cols}")
    else:
        score_t0 = df['mmse_t0']
        score_t1 = df['mmse_t1']

    # Calculate change (T1 - T0). Note: T1 is follow-up, T0 is baseline.
    # Decline means score went DOWN, so T1 < T0.
    # Label 1 if (T0 - T1) >= threshold
    change = score_t0 - score_t1
    df['decline'] = (change >= threshold).astype(int)

    # Check for class balance
    logger.info(f"Class distribution: {df['decline'].value_counts().to_dict()}")
    if df['decline'].sum() == 0 or df['decline'].sum() == len(df):
        logger.warning("Severe class imbalance detected (all 0 or all 1). Results may be unreliable.")

    return df

def collinearity_filter(X: np.ndarray, y: np.ndarray, threshold: float = 0.95) -> Tuple[np.ndarray, List[int]]:
    """
    Remove features with correlation > threshold.
    Keeps the feature with higher variance.
    Returns filtered X and list of kept indices.
    """
    if X.shape[1] <= 1:
        return X, list(range(X.shape[1]))

    corr_matrix = np.corrcoef(X.T)
    np.fill_diagonal(corr_matrix, 0) # Ignore self-correlation
    
    # Mask for high correlation
    high_corr = np.abs(corr_matrix) > threshold

    # Find pairs
    rows, cols = np.where(high_corr)
    pairs = list(zip(rows, cols))
    
    # Deduplicate (since matrix is symmetric)
    unique_pairs = []
    seen = set()
    for r, c in pairs:
        if r < c:
            unique_pairs.append((r, c))
            seen.add((r, c))

    # Calculate variance for all features
    variances = np.var(X, axis=0)

    # Mark features to remove
    to_remove = set()
    for r, c in unique_pairs:
        if r in to_remove or c in to_remove:
            continue
        
        # Keep the one with higher variance
        if variances[r] >= variances[c]:
            to_remove.add(c)
        else:
            to_remove.add(r)

    keep_indices = [i for i in range(X.shape[1]) if i not in to_remove]
    logger.info(f"Collinearity check: removed {len(to_remove)} features, kept {len(keep_indices)}")
    
    return X[:, keep_indices], keep_indices

def inner_cv_pipeline(X: np.ndarray, y: np.ndarray, params: Dict[str, Any]) -> float:
    """
    Inner CV pipeline: Collinearity -> Variance Threshold -> RFE -> RF
    Returns mean ROC-AUC score.
    """
    # 1. Collinearity Check
    X_coll, kept_indices = collinearity_filter(X, y)
    
    if X_coll.shape[1] == 0:
        return 0.0 # Fail gracefully

    # 2. Variance Thresholding
    vt = VarianceThreshold(threshold=0.01)
    X_var = vt.fit_transform(X_coll)
    
    if X_var.shape[1] == 0:
        return 0.0

    # 3. RFE (Select <= 20 features)
    n_features_to_select = min(20, X_var.shape[1])
    base_rf = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=RANDOM_SEED)
    rfe = RFE(estimator=base_rf, n_features_to_select=n_features_to_select, step=1)
    X_rfe = rfe.fit_transform(X_var, y)

    # 4. Fit RF with specific params
    rf = RandomForestClassifier(
        n_estimators=params['n_estimators'],
        max_depth=params['max_depth'],
        random_state=RANDOM_SEED,
        n_jobs=2 # Use 2 cores for parallelism
    )
    
    # Simple cross-validation for score
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
    scores = []
    
    for train_idx, test_idx in skf.split(X_rfe, y):
        X_tr, X_te = X_rfe[train_idx], X_rfe[test_idx]
        y_tr, y_te = y[train_idx], y[test_idx]
        
        rf.fit(X_tr, y_tr)
        # Check if we have both classes in test set for AUC
        if len(np.unique(y_te)) < 2:
            continue
        
        y_proba = rf.predict_proba(X_te)[:, 1]
        auc = roc_auc_score(y_te, y_proba)
        scores.append(auc)
    
    if not scores:
        return 0.0
    
    return np.mean(scores)

def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray) -> Tuple[Any, Dict[str, Any], List[Dict]]:
    """
    Full Nested CV:
    Outer: 5-fold
    Inner: Grid Search with the pipeline defined in inner_cv_pipeline
    """
    logger.info("Starting Nested Cross-Validation")
    
    # Check memory
    if not check_memory_limit():
        raise MemoryError("Memory limit exceeded before training")

    # Grid Search Parameters
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 10, None]
    }

    # Custom scorer for inner loop
    # We use a wrapper that calls inner_cv_pipeline
    def inner_cv_scorer(estimator, X, y):
        # The estimator is just a placeholder here; the logic is in inner_cv_pipeline
        # We pass the params from the estimator's params (if it were a real estimator)
        # But since we are doing manual grid search over the pipeline logic:
        return inner_cv_pipeline(X, y, estimator.get_params())

    # Manual Grid Search to control the inner pipeline strictly
    best_score = -1
    best_params = None
    
    logger.info("Performing Grid Search over inner pipeline...")
    
    # We need to iterate the grid manually because the pipeline is custom
    # We use a simple 3-fold CV inside the grid search
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    
    # To save time, we will do the grid search on the FULL data for the inner loop selection
    # and then evaluate the chosen params on the outer fold.
    # However, strict nested CV requires inner CV on the TRAIN fold of the outer loop.
    
    outer_results = []
    best_outer_score = -1
    best_outer_model = None
    best_outer_params = None

    # Pre-calculate grid candidates
    candidates = []
    for n_est in param_grid['n_estimators']:
        for max_d in param_grid['max_depth']:
            candidates.append({'n_estimators': n_est, 'max_depth': max_d})

    logger.info(f"Testing {len(candidates)} parameter combinations in nested CV.")

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_tr, X_te = X[train_idx], X[test_idx]
        y_tr, y_te = y[train_idx], y[test_idx]

        # Inner Loop: Find best params on training fold
        best_inner_score = -1
        best_inner_params = None

        for params in candidates:
            score = inner_cv_pipeline(X_tr, y_tr, params)
            if score > best_inner_score:
                best_inner_score = score
                best_inner_params = params

        logger.info(f"Outer Fold {fold_idx}: Best Inner Params={best_inner_params}, Score={best_inner_score:.4f}")

        # Train final model on training fold with best params
        # We re-run the full pipeline (Collinearity -> Var -> RFE -> RF)
        # 1. Collinearity
        X_tr_coll, _ = collinearity_filter(X_tr, y_tr)
        # 2. Variance
        vt = VarianceThreshold(threshold=0.01)
        X_tr_var = vt.fit_transform(X_tr_coll)
        # 3. RFE
        n_sel = min(20, X_tr_var.shape[1])
        base_rf = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=RANDOM_SEED)
        rfe = RFE(estimator=base_rf, n_features_to_select=n_sel, step=1)
        X_tr_rfe = rfe.fit_transform(X_tr_var, y_tr)
        
        # 4. RF
        final_rf = RandomForestClassifier(
            n_estimators=best_inner_params['n_estimators'],
            max_depth=best_inner_params['max_depth'],
            random_state=RANDOM_SEED,
            n_jobs=2
        )
        final_rf.fit(X_tr_rfe, y_tr)

        # Evaluate on test fold
        # Apply same transforms to test
        # Note: Collinearity indices must be derived from TRAIN, applied to TEST
        # But collinearity_filter recomputes from X. In strict nested CV, 
        # we should derive the mask from X_tr and apply to X_te.
        # Our function recomputes. To be safe, we assume the structure is stable enough 
        # or we re-run the filter on X_te (which is slightly biased but standard for small N).
        # Strictly: We need to save the 'kept_indices' from X_tr and apply to X_te.
        # Let's modify the flow slightly for strictness:
        
        # Re-do collinearity on X_tr to get mask
        X_tr_coll, kept_indices = collinearity_filter(X_tr, y_tr)
        X_te_coll = X_te[:, kept_indices]
        
        # Variance
        vt = VarianceThreshold(threshold=0.01)
        X_te_var = vt.fit_transform(X_te_coll) # Fit on test? No, fit on train.
        # Correction: Fit VT on X_tr_var, transform X_te_var
        # But we lost X_tr_var. Let's refactor slightly inside the loop for correctness.
        
        # Refactored Inner/Outer logic for strictness:
        # 1. Collinearity on X_tr -> mask
        X_tr_coll, kept_indices = collinearity_filter(X_tr, y_tr)
        X_te_coll = X_te[:, kept_indices]
        
        # 2. Variance on X_tr_coll
        vt = VarianceThreshold(threshold=0.01)
        X_tr_var = vt.fit_transform(X_tr_coll)
        X_te_var = vt.transform(X_te_coll)
        
        # 3. RFE on X_tr_var
        n_sel = min(20, X_tr_var.shape[1])
        base_rf = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=RANDOM_SEED)
        rfe = RFE(estimator=base_rf, n_features_to_select=n_sel, step=1)
        X_tr_rfe = rfe.fit_transform(X_tr_var, y_tr)
        X_te_rfe = rfe.transform(X_te_var)
        
        # 4. RF
        final_rf = RandomForestClassifier(
            n_estimators=best_inner_params['n_estimators'],
            max_depth=best_inner_params['max_depth'],
            random_state=RANDOM_SEED,
            n_jobs=2
        )
        final_rf.fit(X_tr_rfe, y_tr)
        
        # Predict
        if len(np.unique(y_te)) < 2:
            y_pred_proba = np.zeros_like(y_te, dtype=float)
        else:
            y_pred_proba = final_rf.predict_proba(X_te_rfe)[:, 1]
        
        auc = roc_auc_score(y_te, y_pred_proba) if len(np.unique(y_te)) > 1 else 0.5
        acc = accuracy_score(y_te, (y_pred_proba >= 0.5).astype(int))
        f1 = f1_score(y_te, (y_pred_proba >= 0.5).astype(int))
        
        outer_results.append({
            'fold': fold_idx,
            'auc': auc,
            'accuracy': acc,
            'f1': f1,
            'params': best_inner_params
        })

        if auc > best_outer_score:
            best_outer_score = auc
            best_outer_model = final_rf
            best_outer_params = best_inner_params

    # Average metrics
    mean_auc = np.mean([r['auc'] for r in outer_results])
    mean_acc = np.mean([r['accuracy'] for r in outer_results])
    mean_f1 = np.mean([r['f1'] for r in outer_results])

    logger.info(f"Nested CV Complete. Mean AUC: {mean_auc:.4f}, Acc: {mean_acc:.4f}, F1: {mean_f1:.4f}")

    return best_outer_model, {
        'mean_auc': mean_auc,
        'mean_accuracy': mean_acc,
        'mean_f1': mean_f1,
        'fold_results': outer_results,
        'best_params': best_outer_params
    }, outer_results

def train_final_model(X: np.ndarray, y: np.ndarray, params: Dict[str, Any]) -> Any:
    """Train the final model on full data with best params."""
    logger.info("Training final model on full dataset")
    
    # 1. Collinearity
    X_coll, kept_indices = collinearity_filter(X, y)
    # 2. Variance
    vt = VarianceThreshold(threshold=0.01)
    X_var = vt.fit_transform(X_coll)
    # 3. RFE
    n_sel = min(20, X_var.shape[1])
    base_rf = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=RANDOM_SEED)
    rfe = RFE(estimator=base_rf, n_features_to_select=n_sel, step=1)
    X_rfe = rfe.fit_transform(X_var, y)
    
    # 4. RF
    rf = RandomForestClassifier(
        n_estimators=params['n_estimators'],
        max_depth=params['max_depth'],
        random_state=RANDOM_SEED,
        n_jobs=2
    )
    rf.fit(X_rfe, y)
    
    return rf

def main():
    start_time = time.time()
    logger.info("Starting T023: Train Model with Nested CV")

    # Load data
    if not GRAPH_METRICS_PATH.exists():
        logger.error(f"Graph metrics file not found: {GRAPH_METRICS_PATH}")
        logger.error("Please run code/03_compute_graph_metrics.py first.")
        sys.exit(1)

    df = load_csv(GRAPH_METRICS_PATH)
    logger.info(f"Loaded {len(df)} subjects")

    # Define label
    df = define_decline_label(df)

    # Prepare features and target
    # Exclude non-feature columns
    feature_cols = [c for c in df.columns if c not in ['subject_id', 'mmse_t0', 'mmse_t1', 'moca_t0', 'moca_t1', 'decline']]
    if not feature_cols:
        logger.error("No feature columns found in graph_metrics.csv")
        sys.exit(1)

    X = df[feature_cols].values
    y = df['decline'].values

    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Target distribution: {np.bincount(y)}")

    # Check for class imbalance
    if len(np.unique(y)) < 2:
        logger.error("Only one class present in target. Cannot train classifier.")
        sys.exit(1)

    # Run Nested CV
    model, cv_results, fold_details = train_and_evaluate_nested_cv(X, y)

    # Train final model with best params
    final_model = train_final_model(X, y, cv_results['best_params'])

    # Verify FR-003: Base parameters n_estimators=100, max_depth=None
    # The grid search includes these. We log the final selected params.
    selected_n_est = cv_results['best_params']['n_estimators']
    selected_max_d = cv_results['best_params']['max_depth']
    logger.info(f"Final selected parameters: n_estimators={selected_n_est}, max_depth={selected_max_d}")
    
    if selected_n_est == 100 and selected_max_d is None:
        logger.info("FR-003 Compliance: Base parameters (100, None) were selected.")
    else:
        logger.warning(f"FR-003 Compliance: Base parameters (100, None) were NOT selected. Selected: {selected_n_est}, {selected_max_d}")

    # Save model
    ensure_dir(MODEL_OUTPUT_PATH.parent)
    joblib.dump(final_model, MODEL_OUTPUT_PATH)
    logger.info(f"Model saved to {MODEL_OUTPUT_PATH}")

    # Prepare performance report
    report = {
        'status': 'success',
        'nested_cv_results': cv_results,
        'fold_details': fold_details,
        'final_params': cv_results['best_params'],
        'runtime_seconds': time.time() - start_time
    }

    save_json(report, PERFORMANCE_REPORT_PATH)
    logger.info(f"Performance report saved to {PERFORMANCE_REPORT_PATH}")

    logger.info("T023 completed successfully.")

if __name__ == "__main__":
    main()