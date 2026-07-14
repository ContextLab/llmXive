import os
import sys
import json
import time
import warnings
import logging
from pathlib import Path
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
from joblib import Parallel, delayed
import joblib

# Import utilities from project structure
from utils.logger import get_logger
from utils.stats import calculate_correlation_matrix, calculate_feature_variance, filter_low_variance_features
from utils.io import load_dataframe, ensure_dir, save_json

# Constants
RANDOM_SEED = 42
DECLINE_THRESHOLD = 3  # Points drop for decline label
MAX_FEATURES = 20
CORRELATION_THRESHOLD = 0.95
VARIANCE_THRESHOLD = 0.01
RAM_LIMIT_GB = 7.0
N_ESTIMATORS_GRID = [50, 100, 200]
MAX_DEPTH_GRID = [5, 10, None]
OUTER_FOLDS = 5
INNER_FOLDS = 3
N_JOBS = 2

logger = get_logger(__name__)

def define_decline_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    Define the decline label based on MMSE/MOCA score drop >= 3 points.
    Expects columns: 'subject_id', 'score_baseline', 'score_followup'
    Returns dataframe with added 'decline' column (1 if drop >= 3, else 0).
    """
    if 'score_baseline' not in df.columns or 'score_followup' not in df.columns:
        logger.error("Missing required score columns for decline label definition.")
        raise ValueError("Missing required score columns.")

    df = df.copy()
    df['score_drop'] = df['score_baseline'] - df['score_followup']
    df['decline'] = (df['score_drop'] >= DECLINE_THRESHOLD).astype(int)
    
    # Check for class imbalance or lack of positive cases
    if df['decline'].sum() == 0:
        logger.warning("No subjects with cognitive decline (drop >= 3) found in dataset.")
    elif df['decline'].sum() == len(df):
        logger.warning("All subjects show cognitive decline.")
    
    return df

def collinearity_filter(X: np.ndarray, feature_names: list, threshold: float = CORRELATION_THRESHOLD) -> tuple:
    """
    Remove features with Pearson correlation > threshold, keeping the one with higher variance.
    Returns filtered X and updated feature_names.
    """
    if X.shape[1] == 0:
        return X, feature_names

    corr_matrix = calculate_correlation_matrix(X)
    variances = calculate_feature_variance(X)
    
    to_drop = set()
    n_features = X.shape[1]
    
    for i in range(n_features):
        if i in to_drop:
            continue
        for j in range(i + 1, n_features):
            if j in to_drop:
                continue
            if abs(corr_matrix[i, j]) > threshold:
                # Keep higher variance, drop lower
                if variances[i] >= variances[j]:
                    to_drop.add(j)
                else:
                    to_drop.add(i)
    
    keep_indices = [i for i in range(n_features) if i not in to_drop]
    filtered_X = X[:, keep_indices]
    filtered_names = [feature_names[i] for i in keep_indices]
    
    logger.info(f"Collinearity filter: removed {len(to_drop)} features, kept {len(filtered_names)}")
    return filtered_X, filtered_names

def inner_cv_pipeline(X, y, param_grid, feature_names):
    """
    Inner CV pipeline: Collinearity check -> Variance Threshold -> RFE -> Random Forest.
    Returns best model and selected features.
    """
    # 1. Collinearity Filter
    X_clean, names_clean = collinearity_filter(X, feature_names)
    
    if X_clean.shape[1] == 0:
        raise ValueError("All features removed by collinearity filter.")

    # 2. Variance Threshold
    vt = VarianceThreshold(threshold=VARIANCE_THRESHOLD)
    X_var = vt.fit_transform(X_clean)
    names_var = [n for n, v in zip(names_clean, vt.variances_) if v > VARIANCE_THRESHOLD]
    
    if X_var.shape[1] == 0:
        raise ValueError("All features removed by variance threshold.")

    # 3. RFE to select <= MAX_FEATURES
    n_features_to_select = min(MAX_FEATURES, X_var.shape[1])
    base_rf = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=RANDOM_SEED, n_jobs=1)
    rfe = RFE(estimator=base_rf, n_features_to_select=n_features_to_select, step=1)
    X_rfe = rfe.fit_transform(X_var)
    selected_mask = rfe.support_
    names_final = [n for n, m in zip(names_var, selected_mask) if m]
    
    logger.info(f"RFE selected {len(names_final)} features: {names_final}")

    # 4. Grid Search for RF hyperparameters
    rf = RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=1)
    cv_inner = StratifiedKFold(n_splits=INNER_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=cv_inner,
        scoring='roc_auc',
        n_jobs=N_JOBS,
        refit=True
    )
    
    grid_search.fit(X_rfe, y_coll)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Log compliance with FR-003 (Base Parameters: n_estimators=100, max_depth=None)
    if best_params.get('n_estimators') == 100 and best_params.get('max_depth') is None:
        logger.info("FR-003 Compliance: Best parameters include n_estimators=100, max_depth=None.")
    else:
        logger.warning(f"FR-003 Compliance: Best parameters are {best_params}, not the base set.")
    
    # We need to return a pipeline that includes the feature selection steps for prediction
    # However, for nested CV scoring, we just need the best model and the selection logic.
    # To make it reusable, we return the fitted RFE and VT along with the model.
    # But for the outer loop score, we just need the estimator.
    # We will wrap the whole thing in a custom object or re-run the selection in the outer loop?
    # Standard practice: The pipeline must be consistent.
    # Let's return the full pipeline components.
    return best_model, best_params, rfe, vt, names_final

def train_and_evaluate_nested_cv(X, y, feature_names, param_grid):
    """
    Perform nested cross-validation.
    Outer: 5-fold. Inner: Grid Search with feature selection.
    Returns list of outer fold scores and best model from the full data (optional).
    """
    outer_cv = StratifiedKFold(n_splits=OUTER_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    outer_scores = []
    all_selected_features = set()
    
    logger.info(f"Starting Nested CV with {OUTER_FOLDS} outer folds, {INNER_FOLDS} inner folds.")
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        logger.info(f"Processing Outer Fold {fold_idx + 1}/{OUTER_FOLDS}")
        
        # Run inner pipeline on training data
        best_model, best_params, rfe_fitted, vt_fitted, selected_names = inner_cv_pipeline(
            X_train, y_train, param_grid, feature_names
        )
        
        all_selected_features.update(selected_names)
        
        # Apply the SAME feature selection to test data
        # 1. Variance Threshold (re-fit on train, transform test)
        X_train_var = vt_fitted.transform(X_train)
        X_test_var = vt_fitted.transform(X_test)
        
        # 2. RFE (re-fit on train, transform test)
        X_train_rfe = rfe_fitted.transform(X_train_var)
        X_test_rfe = rfe_fitted.transform(X_test_var)
        
        # 3. Predict
        y_pred = best_model.predict(X_test_rfe)
        y_pred_proba = best_model.predict_proba(X_test_rfe)[:, 1]
        
        # Check if we can compute ROC AUC (need at least 2 classes in test)
        if len(np.unique(y_test)) > 1:
            try:
                auc = roc_auc_score(y_test, y_pred_proba)
                outer_scores.append(auc)
                logger.info(f"  Fold {fold_idx + 1} ROC-AUC: {auc:.4f}")
            except Exception as e:
                logger.warning(f"  Fold {fold_idx + 1} ROC-AUC failed: {e}")
                outer_scores.append(np.nan)
        else:
            logger.warning(f"  Fold {fold_idx + 1} has only one class in test set. Skipping AUC.")
            outer_scores.append(np.nan)
    
    return outer_scores, list(all_selected_features)

def main():
    logger.info("Starting model training (T023).")
    
    # Paths
    data_dir = Path("data/processed")
    graph_metrics_path = data_dir / "graph_metrics.csv"
    eligible_subjects_path = data_dir / "eligible_subjects.csv"
    output_model_path = data_dir / "model.pkl"
    output_report_path = data_dir / "performance_report.json"
    
    # Check inputs
    if not graph_metrics_path.exists():
        logger.error(f"Graph metrics file not found: {graph_metrics_path}")
        logger.error("Please run code/03_compute_graph_metrics.py first.")
        sys.exit(1)
    
    if not eligible_subjects_path.exists():
        logger.error(f"Eligible subjects file not found: {eligible_subjects_path}")
        logger.error("Please run code/01_download_and_filter.py first.")
        sys.exit(1)
    
    # Load Data
    try:
        df_metrics = load_dataframe(graph_metrics_path)
        df_eligible = load_dataframe(eligible_subjects_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    # Merge to get features and labels
    # Assuming graph_metrics has 'subject_id' and metric columns
    # Eligible has 'subject_id', 'score_baseline', 'score_followup'
    df = pd.merge(df_metrics, df_eligible[['subject_id', 'score_baseline', 'score_followup']], on='subject_id', how='inner')
    
    if df.empty:
        logger.error("No overlapping subjects found between metrics and eligible list.")
        sys.exit(1)
    
    # Define Decline Label
    df = define_decline_label(df)
    
    # Prepare X and y
    # Exclude non-feature columns
    feature_cols = [c for c in df.columns if c not in ['subject_id', 'score_baseline', 'score_followup', 'score_drop', 'decline']]
    X = df[feature_cols].values
    y = df['decline'].values
    feature_names = feature_cols
    
    logger.info(f"Dataset shape: {X.shape}, Decline rate: {y.mean():.2f}")
    
    if len(np.unique(y)) < 2:
        logger.error("Cannot train model: Only one class present in labels.")
        sys.exit(1)
    
    # Grid Search Parameters
    param_grid = {
        'n_estimators': N_ESTIMATORS_GRID,
        'max_depth': MAX_DEPTH_GRID
    }
    
    # Train with Nested CV
    start_time = time.time()
    try:
        outer_scores, selected_features = train_and_evaluate_nested_cv(X, y, feature_names, param_grid)
    except Exception as e:
        logger.error(f"Nested CV failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    end_time = time.time()
    
    # Calculate mean and std
    valid_scores = [s for s in outer_scores if not np.isnan(s)]
    if valid_scores:
        mean_auc = np.mean(valid_scores)
        std_auc = np.std(valid_scores)
    else:
        mean_auc = 0.0
        std_auc = 0.0
    
    logger.info(f"Nested CV Complete. Mean ROC-AUC: {mean_auc:.4f} (+/- {std_auc:.4f})")
    
    # Train final model on all data for saving
    # Re-run the pipeline on full data to get a final model
    logger.info("Training final model on full dataset...")
    final_model, final_params, final_rfe, final_vt, final_names = inner_cv_pipeline(X, y, param_grid, feature_names)
    
    # Save Model
    ensure_dir(output_model_path.parent)
    joblib.dump({
        'model': final_model,
        'rfe': final_rfe,
        'vt': final_vt,
        'feature_names': final_names,
        'params': final_params,
        'decline_threshold': DECLINE_THRESHOLD
    }, output_model_path)
    logger.info(f"Model saved to {output_model_path}")
    
    # Save Report
    report = {
        'mean_roc_auc': float(mean_auc),
        'std_roc_auc': float(std_auc),
        'fold_scores': [float(s) if not np.isnan(s) else None for s in outer_scores],
        'runtime_seconds': float(end_time - start_time),
        'selected_features': final_names,
        'final_params': final_params,
        'fr_003_compliance': (final_params.get('n_estimators') == 100 and final_params.get('max_depth') is None)
    }
    
    with open(output_report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Performance report saved to {output_report_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())