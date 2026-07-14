import os
import sys
import json
import time
import warnings
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler
from joblib import dump
import psutil

# Import utilities from existing API surface
from utils.logger import get_logger
from utils.io import load_csv, save_json, ensure_dir
from utils.stats import calculate_correlation_matrix, calculate_feature_variance, filter_low_variance_features

# Constants
RANDOM_SEED = 42
DECLINE_THRESHOLD = 3
MEMORY_LIMIT_GB = 7.0
MAX_FEATURES = 20
CORRELATION_THRESHOLD = 0.95
VARIANCE_THRESHOLD = 0.01

# Grid search parameters
PARAM_GRID = {
    'rf__n_estimators': [50, 100, 200],
    'rf__max_depth': [5, 10, None]
}

def get_logger_wrapper(name):
    return get_logger(name)

def get_memory_usage_gb():
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 ** 3

def check_memory_limit(limit_gb=MEMORY_LIMIT_GB):
    """Check if current memory usage exceeds limit."""
    current = get_memory_usage_gb()
    if current > limit_gb:
        raise MemoryError(f"Memory usage {current:.2f}GB exceeds limit {limit_gb}GB")
    return current

def define_decline_label(df, score_col='delta_score'):
    """
    Define the decline label based on score drop.
    FR-003 Compliance: Ensure decline is defined as drop >= 3 points.
    """
    if score_col not in df.columns:
        raise ValueError(f"Column '{score_col}' not found in data. Available: {df.columns.tolist()}")
    
    # Binary classification: 1 if decline (drop >= 3), 0 otherwise
    df['decline_label'] = (df[score_col] >= DECLINE_THRESHOLD).astype(int)
    return df

def collinearity_filter(X, y, correlation_threshold=CORRELATION_THRESHOLD):
    """
    Remove highly correlated features (Pearson > threshold).
    Keep the feature with higher variance when a pair is removed.
    """
    if X.shape[1] <= 1:
        return X, list(X.columns)
    
    corr_matrix = calculate_correlation_matrix(X)
    features = X.columns.tolist()
    to_drop = set()
    
    # Find pairs with correlation > threshold
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            feat_i = features[i]
            feat_j = features[j]
            corr_val = corr_matrix.loc[feat_i, feat_j]
            
            if abs(corr_val) > correlation_threshold:
                # Calculate variance for both features
                var_i = X[feat_i].var()
                var_j = X[feat_j].var()
                
                # Keep the one with higher variance, drop the other
                if var_i >= var_j:
                    to_drop.add(feat_j)
                else:
                    to_drop.add(feat_i)
    
    # Drop features
    features_to_keep = [f for f in features if f not in to_drop]
    X_filtered = X[features_to_keep]
    
    return X_filtered, features_to_keep

def inner_cv_pipeline(X, y, param_grid=PARAM_GRID, n_jobs=2):
    """
    Perform inner CV with:
    1. Collinearity check (exclude features with correlation > 0.95, keep higher variance)
    2. Variance Thresholding (variance > 0.01)
    3. RFE to select <= 20 features
    4. Random Forest Grid Search
    
    Returns best model and best params.
    """
    # Step 1: Variance Thresholding
    vt = VarianceThreshold(threshold=VARIANCE_THRESHOLD)
    X_vt = vt.fit_transform(X)
    # Get feature names after variance thresholding
    vt_mask = vt.get_support()
    X_vt_df = pd.DataFrame(X_vt, columns=[col for col, keep in zip(X.columns, vt_mask) if keep], index=X.index)
    
    if X_vt_df.shape[1] == 0:
        raise ValueError("All features dropped by variance thresholding.")

    # Step 2: Collinearity filter
    X_coll, kept_features = collinearity_filter(X_vt_df, y)
    
    if X_coll.shape[1] == 0:
        raise ValueError("All features dropped by collinearity filter.")

    # Step 3: RFE to select <= 20 features
    # Use a simple RF for RFE
    rfe_base = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, max_depth=None)
    rfe = RFE(estimator=rfe_base, n_features_to_select=min(MAX_FEATURES, X_coll.shape[1]))
    X_rfe = rfe.fit_transform(X_coll, y)
    
    # Get feature names after RFE
    rfe_mask = rfe.get_support()
    X_rfe_df = pd.DataFrame(X_rfe, columns=[col for col, keep in zip(X_coll.columns, rfe_mask) if keep], index=X.index)
    
    if X_rfe_df.shape[1] == 0:
        raise ValueError("All features dropped by RFE.")

    # Step 4: Grid Search with Nested CV structure (inner loop)
    # Create pipeline: Scaling -> RF
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(random_state=RANDOM_SEED))
    ])

    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
    
    grid_search = GridSearchCV(
        pipeline, 
        param_grid, 
        cv=inner_cv, 
        scoring='roc_auc',
        n_jobs=n_jobs,
        refit=True
    )
    
    grid_search.fit(X_rfe_df, y)
    
    return grid_search.best_estimator_, grid_search.best_params_

def train_and_evaluate_nested_cv(X, y, outer_cv_n_splits=5, n_jobs=2):
    """
    Perform Nested Cross-Validation:
    - Outer: 5-fold CV for evaluation
    - Inner: Grid Search with feature selection
    
    Returns:
      - List of AUC scores per fold
      - List of F1 scores per fold
      - List of Accuracy scores per fold
      - Best params found in outer loop (aggregated)
    """
    outer_cv = StratifiedKFold(n_splits=outer_cv_n_splits, shuffle=True, random_state=RANDOM_SEED)
    
    auc_scores = []
    f1_scores = []
    acc_scores = []
    all_best_params = []

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Run inner CV pipeline to get best model
        best_model, best_params = inner_cv_pipeline(X_train, y_train, n_jobs=n_jobs)
        all_best_params.append(best_params)
        
        # Evaluate on test fold
        y_pred_proba = best_model.predict_proba(X_test)[:, 1]
        y_pred = best_model.predict(X_test)
        
        auc = roc_auc_score(y_test, y_pred_proba)
        f1 = f1_score(y_test, y_pred)
        acc = accuracy_score(y_test, y_pred)
        
        auc_scores.append(auc)
        f1_scores.append(f1)
        acc_scores.append(acc)
        
        logging.info(f"Fold {fold_idx + 1}: AUC={auc:.4f}, F1={f1:.4f}, Acc={acc:.4f}")

    return {
        'auc_scores': auc_scores,
        'f1_scores': f1_scores,
        'acc_scores': acc_scores,
        'mean_auc': np.mean(auc_scores),
        'mean_f1': np.mean(f1_scores),
        'mean_acc': np.mean(acc_scores),
        'std_auc': np.std(auc_scores),
        'std_f1': np.std(f1_scores),
        'std_acc': np.std(acc_scores),
        'all_best_params': all_best_params
    }

def train_final_model(X, y, param_grid=PARAM_GRID, n_jobs=2):
    """
    Train final model on full data using best params from grid search.
    Includes full pipeline: Variance Threshold -> Collinearity -> RFE -> RF.
    """
    # 1. Variance Threshold
    vt = VarianceThreshold(threshold=VARIANCE_THRESHOLD)
    X_vt = vt.fit_transform(X)
    vt_mask = vt.get_support()
    X_vt_df = pd.DataFrame(X_vt, columns=[col for col, keep in zip(X.columns, vt_mask) if keep], index=X.index)
    
    # 2. Collinearity
    X_coll, _ = collinearity_filter(X_vt_df, y)
    
    # 3. RFE
    rfe_base = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, max_depth=None)
    rfe = RFE(estimator=rfe_base, n_features_to_select=min(MAX_FEATURES, X_coll.shape[1]))
    X_rfe = rfe.fit_transform(X_coll, y)
    rfe_mask = rfe.get_support()
    X_rfe_df = pd.DataFrame(X_rfe, columns=[col for col, keep in zip(X_coll.columns, rfe_mask) if keep], index=X.index)
    
    # 4. Grid Search to find best params (using all data for final selection logic)
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(random_state=RANDOM_SEED))
    ])
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    grid_search = GridSearchCV(
        pipeline, 
        param_grid, 
        cv=cv, 
        scoring='roc_auc',
        n_jobs=n_jobs,
        refit=True
    )
    
    grid_search.fit(X_rfe_df, y)
    
    final_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    return final_model, best_params, {
        'vt_mask': vt_mask.tolist(),
        'collinearity_drop': [c for c in X_vt_df.columns if c not in X_coll.columns],
        'rfe_drop': [c for c in X_coll.columns if c not in X_rfe_df.columns],
        'final_features': X_rfe_df.columns.tolist()
    }

def main():
    logger = get_logger('04_train_model')
    logger.info("Starting T023: Train Model with Nested CV")
    
    # Paths
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / 'data' / 'processed'
    metrics_file = data_dir / 'graph_metrics.csv'
    model_file = data_dir / 'model.pkl'
    report_file = data_dir / 'performance_report.json'
    
    ensure_dir(data_dir)
    
    # Check memory
    check_memory_limit()
    
    # Load data
    logger.info(f"Loading graph metrics from {metrics_file}")
    if not metrics_file.exists():
        logger.error(f"Graph metrics file not found: {metrics_file}")
        logger.error("Please run code/03_compute_graph_metrics.py first.")
        sys.exit(1)
    
    df = load_csv(str(metrics_file))
    
    # Define decline label
    logger.info("Defining decline label (drop >= 3 points)")
    df = define_decline_label(df)
    
    # Prepare features and target
    # Assume columns starting with 'metric_' are features
    feature_cols = [col for col in df.columns if col.startswith('metric_')]
    if not feature_cols:
        logger.error("No features found starting with 'metric_'. Columns: " + str(df.columns.tolist()))
        sys.exit(1)
    
    X = df[feature_cols]
    y = df['decline_label']
    
    # Check class balance
    class_counts = y.value_counts()
    logger.info(f"Class distribution: {class_counts.to_dict()}")
    if len(class_counts) < 2:
        logger.error("Only one class found in target. Cannot train classifier.")
        sys.exit(1)
    
    # Train with Nested CV
    logger.info("Starting Nested Cross-Validation (5 outer folds, grid search inner)")
    start_time = time.time()
    
    try:
        results = train_and_evaluate_nested_cv(X, y, outer_cv_n_splits=5, n_jobs=2)
    except Exception as e:
        logger.error(f"Error during Nested CV: {e}")
        raise
    
    elapsed_time = time.time() - start_time
    logger.info(f"Nested CV completed in {elapsed_time:.2f} seconds")
    
    # Log FR-003 compliance check
    # FR-003: Ensure grid search includes n_estimators=100, max_depth=None
    base_params = {'n_estimators': 100, 'max_depth': None}
    # Check if this combination was tested (it is in PARAM_GRID)
    logger.info(f"Grid search parameters tested: {PARAM_GRID}")
    logger.info(f"FR-003 Compliance: Base params {base_params} are included in grid search.")
    
    # Train final model on full data
    logger.info("Training final model on full dataset")
    final_model, best_params, feature_info = train_final_model(X, y, n_jobs=2)
    
    logger.info(f"Final model best params: {best_params}")
    
    # Save model
    logger.info(f"Saving model to {model_file}")
    dump(final_model, str(model_file))
    
    # Prepare report
    report = {
        'nested_cv_results': {
            'mean_auc': float(results['mean_auc']),
            'mean_f1': float(results['mean_f1']),
            'mean_acc': float(results['mean_acc']),
            'std_auc': float(results['std_auc']),
            'std_f1': float(results['std_f1']),
            'std_acc': float(results['std_acc']),
            'fold_auc_scores': [float(x) for x in results['auc_scores']],
            'fold_f1_scores': [float(x) for x in results['f1_scores']],
            'fold_acc_scores': [float(x) for x in results['acc_scores']],
            'runtime_seconds': elapsed_time
        },
        'final_model_params': best_params,
        'fr003_compliance': {
            'tested_base_params': base_params,
            'status': 'COMPLIANT'
        },
        'feature_selection': feature_info,
        'class_distribution': {str(k): int(v) for k, v in y.value_counts().items()}
    }
    
    # Save report
    logger.info(f"Saving performance report to {report_file}")
    save_json(report, str(report_file))
    
    logger.info("T023 completed successfully.")
    logger.info(f"Final ROC-AUC: {results['mean_auc']:.4f} (+/- {results['std_auc']:.4f})")

if __name__ == '__main__':
    main()