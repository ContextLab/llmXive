from __future__ import annotations

import argparse
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
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.feature_selection import VarianceThreshold, RFE
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler
from joblib import Parallel, delayed
from utils.logger import get_logger, log_operation
from utils.stats import check_collinearity, calculate_feature_variance, filter_low_variance_features
from utils.io import load_csv, save_json, save_pickle

logger = get_logger("train_model")

# Constants
DATA_DIR = Path("data/processed")
GRAPH_METRICS_FILE = DATA_DIR / "graph_metrics.csv"
ELIGIBLE_SUBJECTS_FILE = DATA_DIR / "eligible_subjects.csv"
MODEL_FILE = DATA_DIR / "model.pkl"
CV_RESULTS_FILE = DATA_DIR / "cv_results.json"
MODEL_PARAMS_FILE = DATA_DIR / "model_params.json"

EXIT_CODE_NO_DATA = 3
EXIT_CODE_SUCCESS = 0

def load_features_and_labels(threshold: int = 3) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load graph metrics and generate decline labels based on MMSE/MOCA drop.
    Returns (X, y) where y is 1 if drop >= threshold, else 0.
    """
    if not GRAPH_METRICS_FILE.exists():
        logger.log("error", message=f"Graph metrics file not found: {GRAPH_METRICS_FILE}")
        sys.exit(EXIT_CODE_NO_DATA)

    if not ELIGIBLE_SUBJECTS_FILE.exists():
        logger.log("error", message=f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_FILE}")
        sys.exit(EXIT_CODE_NO_DATA)

    # Load graph metrics
    df = load_csv(GRAPH_METRICS_FILE)
    eligible_df = load_csv(ELIGIBLE_SUBJECTS_FILE)

    # Ensure we only use eligible subjects
    eligible_ids = set(eligible_df['subject_id'].tolist())
    df = df[df['subject_id'].isin(eligible_ids)]

    if df.empty:
        logger.log("error", message="No eligible subjects found in graph metrics.")
        sys.exit(EXIT_CODE_NO_DATA)

    # Load longitudinal data for label generation
    # Assuming participants.tsv or similar exists in data/raw/ds000246/
    raw_participants = Path("data/raw/ds000246/participants.tsv")
    if not raw_participants.exists():
        # Fallback: try to find any participants file
        raw_participants = next(Path("data/raw").glob("**/participants.tsv"), None)
        if not raw_participants:
            logger.log("error", message="Participants file not found for label generation.")
            sys.exit(EXIT_CODE_NO_DATA)

    raw_df = pd.read_csv(raw_participants, sep='\t')

    # Logic to calculate decline: drop >= threshold points
    # We assume the raw_df has columns: subject_id, MMSE_baseline, MMSE_followup (or similar)
    # If columns are not exactly named, we try to infer or use a generic approach
    # For robustness, we look for columns containing 'MMSE' or 'MOCA'
    mmse_cols = [c for c in raw_df.columns if 'MMSE' in c.upper()]
    moca_cols = [c for c in raw_df.columns if 'MOCA' in c.upper()]

    if not mmse_cols and not moca_cols:
        logger.log("error", message="No MMSE or MOCA columns found in participants file.")
        sys.exit(EXIT_CODE_NO_DATA)

    # Assume first two columns of the same type are baseline and followup
    score_cols = mmse_cols if mmse_cols else moca_cols
    if len(score_cols) < 2:
        logger.log("error", message="Not enough score columns to calculate decline.")
        sys.exit(EXIT_CODE_NO_DATA)

    # Sort columns to ensure consistent ordering (e.g., by name or assumption)
    # This is a simplification; in a real scenario, we'd parse the BIDS metadata
    score_cols = sorted(score_cols)
    baseline_col = score_cols[0]
    followup_col = score_cols[1]

    # Merge with raw data to get scores
    df = df.merge(raw_df[['subject_id', baseline_col, followup_col]], on='subject_id', how='inner')

    # Calculate drop
    df['score_drop'] = df[baseline_col] - df[followup_col]

    # Generate label: 1 if drop >= threshold, else 0
    df['decline_label'] = (df['score_drop'] >= threshold).astype(int)

    # Features are the graph metrics (excluding subject_id and score_drop)
    feature_cols = [c for c in df.columns if c not in ['subject_id', 'score_drop', 'decline_label']]
    X = df[feature_cols].dropna()
    y = df.loc[X.index, 'decline_label']

    if X.empty:
        logger.log("error", message="No valid features after dropping NaNs.")
        sys.exit(EXIT_CODE_NO_DATA)

    logger.log("load_data", subjects=len(X), features=len(feature_cols), positive_rate=y.mean())
    return X, y

class CollinearityTransformer:
    """
    Feature selection transformer that removes collinear features (corr > 0.95).
    Keeps the feature with higher variance.
    Must be fit ONLY on the training fold.
    """
    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.features_to_keep = None

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None):
        if X.shape[1] == 0:
            return self

        corr_matrix = X.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = [column for column in upper.columns if any(upper[column] > self.threshold)]

        # For each pair, keep the one with higher variance
        if to_drop:
            variances = X.var()
            # We need to know which to keep. The requirement says: keep higher variance.
            # If A and B are collinear, and A is in to_drop, we keep B if var(B) > var(A).
            # But 'to_drop' is a list of columns to remove. We need to be careful.
            # A simpler approach: iterate through the upper triangle and drop the one with lower variance.
            final_to_drop = set()
            for col in to_drop:
                # Find the correlated partner
                partners = corr_matrix.index[upper[col] > self.threshold]
                if len(partners) > 0:
                    partner = partners[0]
                    if variances[col] < variances[partner]:
                        final_to_drop.add(col)
                    else:
                        final_to_drop.add(partner)

            self.features_to_keep = [c for c in X.columns if c not in final_to_drop]
        else:
            self.features_to_keep = list(X.columns)

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if self.features_to_keep is None:
            return X
        return X[self.features_to_keep]

def train_single_fold(X_train: pd.DataFrame, y_train: pd.Series, 
                      X_test: pd.DataFrame, y_test: pd.Series, 
                      param_grid: Dict[str, List], threshold: int) -> Dict[str, Any]:
    """
    Train a single fold with nested feature selection and grid search.
    All feature selection MUST be fit only on X_train.
    """
    # Step 1: Collinearity removal (fit on train)
    collinearity_filter = CollinearityTransformer(threshold=0.95)
    X_train_coll = collinearity_filter.fit_transform(X_train)
    X_test_coll = collinearity_filter.transform(X_test)

    if X_train_coll.shape[1] == 0:
        # Fallback if all features dropped
        logger.log("warning", message="All features dropped by collinearity filter. Using original.")
        X_train_coll = X_train
        X_test_coll = X_test

    # Step 2: Variance Thresholding (fit on train)
    var_thresh = VarianceThreshold(threshold=0.01)
    X_train_var = var_thresh.fit_transform(X_train_coll)
    X_test_var = var_thresh.transform(X_test_coll)

    # Convert back to DataFrame to preserve index for RFE
    feature_names = X_train_coll.columns[var_thresh.get_support()]
    X_train_var_df = pd.DataFrame(X_train_var, columns=feature_names, index=X_train.index)
    X_test_var_df = pd.DataFrame(X_test_var, columns=feature_names, index=X_test.index)

    # Step 3: RFE to select <= 20 features (fit on train)
    base_rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rfe = RFE(estimator=base_rf, n_features_to_select=min(20, X_train_var_df.shape[1]), step=1)
    rfe.fit(X_train_var_df, y_train)

    X_train_rfe = rfe.transform(X_train_var_df)
    X_test_rfe = rfe.transform(X_test_var_df)

    # Convert back to DataFrame
    final_feature_names = feature_names[rfe.support_]
    X_train_rfe_df = pd.DataFrame(X_train_rfe, columns=final_feature_names, index=X_train.index)
    X_test_rfe_df = pd.DataFrame(X_test_rfe, columns=final_feature_names, index=X_test.index)

    # Step 4: Grid Search for Random Forest (fit on train)
    rf = RandomForestClassifier(random_state=42)
    grid_search = GridSearchCV(
        rf, 
        param_grid, 
        cv=3, 
        scoring='roc_auc', 
        n_jobs=2,
        refit=True
    )
    grid_search.fit(X_train_rfe_df, y_train)

    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_

    # Evaluate on test
    y_pred_proba = best_model.predict_proba(X_test_rfe_df)[:, 1]
    y_pred = best_model.predict(X_test_rfe_df)

    roc_auc = roc_auc_score(y_test, y_pred_proba)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    return {
        "roc_auc": float(roc_auc),
        "accuracy": float(acc),
        "f1_score": float(f1),
        "best_params": best_params,
        "n_estimators_used": best_params.get('n_estimators'),
        "max_depth_used": best_params.get('max_depth')
    }

def train_and_evaluate_nested_cv(X: pd.DataFrame, y: pd.Series, 
                                 param_grid: Dict[str, List], 
                                 n_folds: int = 5, 
                                 threshold: int = 3) -> List[Dict[str, Any]]:
    """
    Run nested cross-validation.
    Outer loop: StratifiedKFold for evaluation.
    Inner loop: GridSearchCV for hyperparameter tuning + feature selection.
    """
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    results = []

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        fold_result = train_single_fold(X_train, y_train, X_test, y_test, param_grid, threshold)
        fold_result['fold'] = fold_idx + 1
        results.append(fold_result)
        
        logger.log("fold_complete", fold=fold_idx + 1, roc_auc=fold_result['roc_auc'])

    return results

def persist_model(model: Any, path: Path):
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.log("model_saved", path=str(path))

def write_cv_results(results: List[Dict], path: Path):
    save_json(results, path)
    logger.log("cv_results_saved", path=str(path), count=len(results))

def write_model_params(best_params: Dict, path: Path):
    save_json(best_params, path)
    logger.log("model_params_saved", path=str(path))

def train_model(threshold: int = 3):
    """Main training pipeline."""
    start_time = time.time()
    
    # Load data
    X, y = load_features_and_labels(threshold=threshold)
    
    # Define grid
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [None, 10, 20]
    }

    logger.log("training_started", n_samples=len(X), param_grid=param_grid)

    # Run nested CV
    cv_results = train_and_evaluate_nested_cv(X, y, param_grid, n_folds=5, threshold=threshold)

    # Aggregate best params (take the most common or average, but here we just pick the best from the last fold for simplicity)
    # In a real scenario, we might retrain on full data with best params.
    # For now, we'll just save the results and the best params from the grid search of the last fold.
    # Actually, let's aggregate: find the best params across all folds or just take the best from the first fold?
    # The task asks for "model_params.json" containing the best parameters found.
    # We'll take the best params from the fold with the highest ROC-AUC.
    best_fold = max(cv_results, key=lambda x: x['roc_auc'])
    best_params = best_fold['best_params']

    # Write outputs
    write_cv_results(cv_results, CV_RESULTS_FILE)
    write_model_params(best_params, MODEL_PARAMS_FILE)

    # Train a final model on ALL data with best params (for model.pkl)
    # We reuse the pipeline logic but without CV splitting
    # Note: This is a simplification. A full implementation would wrap the whole feature selection + RF in a Pipeline
    # and refit on all data.
    
    # Re-run feature selection on full data (this is acceptable for the final model)
    collinearity_filter = CollinearityTransformer(threshold=0.95)
    X_coll = collinearity_filter.fit_transform(X)
    
    var_thresh = VarianceThreshold(threshold=0.01)
    X_var = var_thresh.fit_transform(X_coll)
    feature_names = X_coll.columns[var_thresh.get_support()]
    X_var_df = pd.DataFrame(X_var, columns=feature_names, index=X.index)
    
    base_rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rfe = RFE(estimator=base_rf, n_features_to_select=min(20, X_var_df.shape[1]), step=1)
    rfe.fit(X_var_df, y)
    
    X_final = pd.DataFrame(rfe.transform(X_var_df), columns=feature_names[rfe.support()], index=X.index)
    
    final_model = RandomForestClassifier(**best_params, random_state=42)
    final_model.fit(X_final, y)
    
    persist_model(final_model, MODEL_FILE)

    elapsed = time.time() - start_time
    logger.log("training_complete", elapsed=elapsed, n_folds=5)
    
    return cv_results, best_params

def main():
    parser = argparse.ArgumentParser(description="Train Random Forest model for cognitive decline prediction.")
    parser.add_argument('--threshold', type=int, default=3, help="Threshold for cognitive decline (default: 3)")
    args = parser.parse_args()

    logger.log("main_start", threshold=args.threshold)
    
    try:
        train_model(threshold=args.threshold)
        logger.log("main_success")
        sys.exit(EXIT_CODE_SUCCESS)
    except Exception as e:
        logger.log("error", message=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
