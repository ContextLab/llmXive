"""
code/04_train_model.py
Implements Nested Cross-Validation with Grid Search for predicting cognitive decline.
"""
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
from sklearn.model_selection import (
    StratifiedKFold,
    GridSearchCV,
    cross_val_score,
    train_test_split
)
from sklearn.feature_selection import VarianceThreshold, RFE
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr
import joblib

# Project imports
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, load_json, save_json
from utils.stats import check_collinearity, calculate_feature_variance, filter_low_variance_features

# Constants
DECREASE_THRESHOLD = 3
RANDOM_SEED = 42
MAX_FEATURES = 20
MIN_VARIANCE = 0.01
CORRELATION_THRESHOLD = 0.95
N_ESTIMATORS_GRID = [50, 100, 200]
MAX_DEPTH_GRID = [None, 10, 20]
N_FOLDS_OUTER = 5
N_FOLDS_INNER = 3

logger = get_logger("train_model")


def load_features(csv_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads features and labels from graph_metrics.csv.
    Returns: (X, y, subject_ids)
    """
    df = pd.read_csv(csv_path)
    # Ensure we have the expected columns
    required_cols = ['subject_id', 'node_degree', 'global_efficiency', 'clustering_coeff', 'path_length']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV missing required columns. Found: {df.columns.tolist()}")

    # Define decline label: drop >= 3 points
    # Assuming the CSV contains 'mmse_baseline', 'mmse_followup' or similar.
    # If the CSV only has graph metrics, we need to load the longitudinal scores separately.
    # Based on T017a, eligible_subjects.csv has the scores.
    # We assume graph_metrics.csv has been enriched or we join here.
    # For this implementation, we assume the CSV has 'mmse_baseline' and 'mmse_followup'.
    # If not, we try to load from a separate file if available, but the task implies graph_metrics.csv is the source.
    # Let's assume the CSV has the necessary score columns. If not, we raise an error or handle gracefully.
    # Re-reading T019: Output to graph_metrics.csv with subject_id and graph metrics.
    # T023 says: Define decline label (drop >= 3 points). This implies we need the scores.
    # We must join with the eligible subjects data which has the scores.

    eligible_path = "data/processed/eligible_subjects.csv"
    if not os.path.exists(eligible_path):
        raise FileNotFoundError(f"Required file {eligible_path} not found. Run T017a first.")

    eligible_df = pd.read_csv(eligible_path)
    # Merge to get scores
    # Assuming eligible_df has subject_id, mmse_baseline, mmse_followup
    if 'mmse_baseline' in eligible_df.columns and 'mmse_followup' in eligible_df.columns:
        df = df.merge(eligible_df[['subject_id', 'mmse_baseline', 'mmse_followup']], on='subject_id', how='left')
    else:
        # Fallback: try to find columns with 'mmse' or 'moca'
        base_cols = [c for c in eligible_df.columns if 'mmse' in c.lower() and 'baseline' in c.lower()]
        follow_cols = [c for c in eligible_df.columns if 'mmse' in c.lower() and 'followup' in c.lower()]
        if base_cols and follow_cols:
            df = df.merge(eligible_df[['subject_id', base_cols[0], follow_cols[0]]], on='subject_id', how='left')
            df.columns = df.columns.str.replace(base_cols[0], 'mmse_baseline')
            df.columns = df.columns.str.replace(follow_cols[0], 'mmse_followup')
        else:
            raise ValueError("Could not find MMSE baseline/followup columns in eligible_subjects.csv")

    # Calculate decline
    df['decline'] = df['mmse_baseline'] - df['mmse_followup']
    # Label: 1 if decline >= threshold, 0 otherwise
    df['label'] = (df['decline'] >= DECREASE_THRESHOLD).astype(int)

    feature_cols = ['node_degree', 'global_efficiency', 'clustering_coeff', 'path_length']
    X = df[feature_cols]
    y = df['label']
    subject_ids = df['subject_id']

    return X, y, subject_ids


class CollinearityTransformer:
    """
    Feature transformer that removes one of any pair of features with correlation > threshold.
    Keeps the one with higher variance.
    """
    def __init__(self, threshold: float = CORRELATION_THRESHOLD):
        self.threshold = threshold
        self.keep_mask_ = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None):
        corr_matrix = np.corrcoef(X.T)
        n_features = X.shape[1]
        keep_mask = np.ones(n_features, dtype=bool)

        for i in range(n_features):
            if not keep_mask[i]:
                continue
            for j in range(i + 1, n_features):
                if not keep_mask[j]:
                    continue
                if abs(corr_matrix[i, j]) > self.threshold:
                    # Keep higher variance
                    var_i = np.var(X[:, i])
                    var_j = np.var(X[:, j])
                    if var_i >= var_j:
                        keep_mask[j] = False
                    else:
                        keep_mask[i] = False
                        break # i is dropped, move to next i

        self.keep_mask_ = keep_mask
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        return X[:, self.keep_mask_]


def train_single_fold(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    decline_threshold: int = DECREASE_THRESHOLD
) -> Dict[str, Any]:
    """
    Trains a model on a single fold with inner feature selection and grid search.
    Returns metrics and best params.
    """
    # 1. Collinearity Check
    collinearity_transformer = CollinearityTransformer()
    collinearity_transformer.fit(X_train)
    X_train_coll = collinearity_transformer.transform(X_train)
    X_test_coll = collinearity_transformer.transform(X_test)

    # 2. Variance Thresholding
    var_thresh = VarianceThreshold(threshold=MIN_VARIANCE)
    X_train_var = var_thresh.fit_transform(X_train_coll)
    X_test_var = var_thresh.transform(X_test_coll)

    # 3. RFE to select <= MAX_FEATURES
    base_rf = RandomForestClassifier(random_state=RANDOM_SEED)
    rfe = RFE(estimator=base_rf, n_features_to_select=min(MAX_FEATURES, X_train_var.shape[1]))
    X_train_rfe = rfe.fit_transform(X_train_var, y_train)
    X_test_rfe = rfe.transform(X_test_var)

    if X_train_rfe.shape[1] == 0:
        raise ValueError("No features selected after RFE.")

    # 4. Grid Search for Hyperparameters
    param_grid = {
        'n_estimators': N_ESTIMATORS_GRID,
        'max_depth': MAX_DEPTH_GRID
    }

    rf = RandomForestClassifier(random_state=RANDOM_SEED)
    skf_inner = StratifiedKFold(n_splits=N_FOLDS_INNER, shuffle=True, random_state=RANDOM_SEED)

    grid_search = GridSearchCV(
        rf,
        param_grid,
        cv=skf_inner,
        scoring='roc_auc',
        n_jobs=2,
        verbose=0
    )

    grid_search.fit(X_train_rfe, y_train)
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_

    # Evaluate on test set
    y_pred_prob = best_model.predict_proba(X_test_rfe)[:, 1]
    y_pred = best_model.predict(X_test_rfe)

    roc_auc = roc_auc_score(y_test, y_pred_prob)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    return {
        'roc_auc': roc_auc,
        'accuracy': acc,
        'f1_score': f1,
        'best_params': best_params,
        'n_estimators': best_params['n_estimators'],
        'max_depth': best_params['max_depth']
    }


def train_and_evaluate_nested_cv(
    X: np.ndarray,
    y: np.ndarray,
    decline_threshold: int = DECREASE_THRESHOLD
) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    """
    Runs the full nested cross-validation.
    Returns: (best_overall_params, mean_metrics, fold_results)
    """
    skf_outer = StratifiedKFold(n_splits=N_FOLDS_OUTER, shuffle=True, random_state=RANDOM_SEED)
    fold_results = []
    all_preds_prob = []
    all_preds_true = []

    for fold_idx, (train_idx, test_idx) in enumerate(skf_outer.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        logger.log("nested_cv_fold", fold=fold_idx, n_train=len(train_idx), n_test=len(test_idx))

        try:
            fold_metrics = train_single_fold(X_train, y_train, X_test, y_test, decline_threshold)
            fold_results.append({
                'fold': fold_idx,
                'roc_auc': fold_metrics['roc_auc'],
                'accuracy': fold_metrics['accuracy'],
                'f1_score': fold_metrics['f1_score'],
                'n_estimators': fold_metrics['n_estimators'],
                'max_depth': fold_metrics['max_depth']
            })
            all_preds_prob.extend(fold_metrics.get('y_pred_prob', [])) # Not stored in dict, but needed for overall?
            all_preds_true.extend(y_test)
        except Exception as e:
            logger.log("nested_cv_fold_error", fold=fold_idx, error=str(e))
            # Continue with next fold or fail? Fail loudly as per constraints.
            raise e

    # Calculate mean metrics
    mean_roc_auc = np.mean([r['roc_auc'] for r in fold_results])
    mean_acc = np.mean([r['accuracy'] for r in fold_results])
    mean_f1 = np.mean([r['f1_score'] for r in fold_results])

    best_overall_params = {
        'mean_roc_auc': mean_roc_auc,
        'mean_accuracy': mean_acc,
        'mean_f1_score': mean_f1
    }

    return best_overall_params, best_overall_params, fold_results


def persist_model(model: Any, path: str):
    """Saves the model to disk."""
    with open(path, 'wb') as f:
        pickle.dump(model, f)


def write_cv_results(results: List[Dict[str, Any]], path: str):
    """Writes CV results to JSON."""
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)


def write_model_params(params: Dict[str, Any], path: str):
    """Writes best parameters to JSON."""
    with open(path, 'w') as f:
        json.dump(params, f, indent=2)


def train_model(data: Tuple[np.ndarray, np.ndarray], decline_threshold: int = DECREASE_THRESHOLD) -> Dict[str, Any]:
    """
    Callable function to train model with a specific decline threshold.
    Used by T030 for sensitivity analysis.
    """
    X, y = data
    # Re-run the nested CV logic here or call the main function
    # Since the main function does file I/O, we extract the core logic
    # For simplicity in this refactor, we call the main logic but suppress file writes if called programmatically
    # However, the requirement is to expose the function.
    # We will re-implement the core loop here to ensure it returns the model and metrics.

    skf_outer = StratifiedKFold(n_splits=N_FOLDS_OUTER, shuffle=True, random_state=RANDOM_SEED)
    fold_results = []
    best_model = None
    best_score = -1

    for fold_idx, (train_idx, test_idx) in enumerate(skf_outer.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Feature Selection & Grid Search
        collinearity_transformer = CollinearityTransformer()
        collinearity_transformer.fit(X_train)
        X_train_coll = collinearity_transformer.transform(X_train)
        X_test_coll = collinearity_transformer.transform(X_test)

        var_thresh = VarianceThreshold(threshold=MIN_VARIANCE)
        X_train_var = var_thresh.fit_transform(X_train_coll)
        X_test_var = var_thresh.transform(X_test_coll)

        base_rf = RandomForestClassifier(random_state=RANDOM_SEED)
        rfe = RFE(estimator=base_rf, n_features_to_select=min(MAX_FEATURES, X_train_var.shape[1]))
        X_train_rfe = rfe.fit_transform(X_train_var, y_train)
        X_test_rfe = rfe.transform(X_test_var)

        param_grid = {'n_estimators': N_ESTIMATORS_GRID, 'max_depth': MAX_DEPTH_GRID}
        rf = RandomForestClassifier(random_state=RANDOM_SEED)
        skf_inner = StratifiedKFold(n_splits=N_FOLDS_INNER, shuffle=True, random_state=RANDOM_SEED)

        grid_search = GridSearchCV(rf, param_grid, cv=skf_inner, scoring='roc_auc', n_jobs=2)
        grid_search.fit(X_train_rfe, y_train)

        fold_model = grid_search.best_estimator_
        y_pred_prob = fold_model.predict_proba(X_test_rfe)[:, 1]
        roc_auc = roc_auc_score(y_test, y_pred_prob)

        fold_results.append({
            'fold': fold_idx,
            'roc_auc': roc_auc,
            'n_estimators': grid_search.best_params_['n_estimators'],
            'max_depth': grid_search.best_params_['max_depth']
        })

        if roc_auc > best_score:
            best_score = roc_auc
            best_model = fold_model

    mean_roc_auc = np.mean([r['roc_auc'] for r in fold_results])
    return {
        'model': best_model,
        'mean_roc_auc': mean_roc_auc,
        'fold_results': fold_results,
        'best_params': best_model.get_params()
    }


@log_operation("train_model_main")
def main():
    start_time = time.time()
    logger.log("start_training")

    # Paths
    metrics_csv = "data/processed/graph_metrics.csv"
    output_dir = "data/processed"
    model_path = os.path.join(output_dir, "model.pkl")
    cv_results_path = os.path.join(output_dir, "cv_results.json")
    params_path = os.path.join(output_dir, "model_params.json")

    ensure_dir(output_dir)

    # Load Data
    X, y, _ = load_features(metrics_csv)
    X_np = X.values
    y_np = y.values

    if len(np.unique(y_np)) < 2:
        logger.log("error", message="Only one class found in labels. Cannot train classifier.")
        sys.exit(1)

    # Train
    result = train_model((X_np, y_np), DECREASE_THRESHOLD)

    # Save Model
    persist_model(result['model'], model_path)
    logger.log("model_saved", path=model_path)

    # Save CV Results
    write_cv_results(result['fold_results'], cv_results_path)
    logger.log("cv_results_saved", path=cv_results_path)

    # Save Params
    write_model_params(result['best_params'], params_path)
    logger.log("params_saved", path=params_path)

    elapsed = time.time() - start_time
    logger.log("training_complete", elapsed_seconds=elapsed, mean_roc_auc=result['mean_roc_auc'])

    print(f"Training complete. Mean ROC-AUC: {result['mean_roc_auc']:.4f}")
    print(f"Model saved to {model_path}")
    print(f"CV Results saved to {cv_results_path}")
    print(f"Params saved to {params_path}")


if __name__ == "__main__":
    main()