"""
code/04_train_model.py
Implements Nested CV with feature selection and Random Forest training.
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
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.model_selection import GridSearchCV, KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from scipy.stats import pearsonr

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from utils.logger import get_logger, log_operation
from utils.stats import check_collinearity, calculate_correlation_matrix, calculate_feature_variance, filter_low_variance_features
from utils.io import load_csv, save_json, save_pickle, ensure_dir

logger = get_logger("train_model")

# Configuration
RANDOM_SEED = 42
DATA_PATH = Path("data/processed/graph_metrics.csv")
ELIGIBLE_PATH = Path("data/processed/eligible_subjects.csv")
OUTPUT_DIR = Path("data/processed")
MODEL_PATH = OUTPUT_DIR / "model.pkl"
CV_RESULTS_PATH = OUTPUT_DIR / "cv_results.json"
MODEL_PARAMS_PATH = OUTPUT_DIR / "model_params.json"

# Grid search parameters
N_ESTIMATORS = [50, 100, 200]
MAX_DEPTH = [5, 10, None]
MAX_FEATURES = 20
CORRELATION_THRESHOLD = 0.95
VARIANCE_THRESHOLD = 0.01
DECLINE_THRESHOLD = 3  # Drop of 3 points in MMSE/MOCA

np.random.seed(RANDOM_SEED)

class CollinearityTransformer:
    """
    Custom transformer to handle collinearity by dropping one of the pair
    with correlation > threshold, keeping the one with higher variance.
    """
    def __init__(self, threshold: float = CORRELATION_THRESHOLD):
        self.threshold = threshold
        self.cols_to_drop: List[str] = []
        self.feature_names_in_: List[str] = []
        self.n_features_in_: int = 0

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None):
        if X.shape[1] == 0:
            return self

        self.feature_names_in_ = list(X.columns)
        self.n_features_in_ = len(self.feature_names_in_)
        corr_matrix = X.corr().abs()
        
        # Upper triangle of correlation matrix
        upper = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        
        # Find features with correlation above threshold
        to_drop = [
            column for column in upper.columns
            if any(upper[column] > self.threshold)
        ]
        
        # For each pair, drop the one with lower variance
        if to_drop:
            variances = X.var()
            # Group by correlation pairs to decide which to drop
            # Simple heuristic: iterate and drop lower variance one
            # We need to be careful not to drop based on already dropped ones
            # So we recalculate based on current set
            current_cols = [c for c in self.feature_names_in_ if c not in to_drop]
            
            # Re-check correlation within remaining set + one from each pair
            # For simplicity, we drop the lower variance feature in each pair
            pairs_to_check = []
            for i, col1 in enumerate(self.feature_names_in_):
                for col2 in self.feature_names_in_[i+1:]:
                    if corr_matrix.loc[col1, col2] > self.threshold:
                        pairs_to_check.append((col1, col2))
            
            cols_to_drop = set()
            for c1, c2 in pairs_to_check:
                if c1 not in cols_to_drop and c2 not in cols_to_drop:
                    v1 = variances.get(c1, 0)
                    v2 = variances.get(c2, 0)
                    if v1 < v2:
                        cols_to_drop.add(c1)
                    else:
                        cols_to_drop.add(c2)
            
            self.cols_to_drop = list(cols_to_drop)
        else:
            self.cols_to_drop = []
        
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.cols_to_drop:
            return X
        cols_to_keep = [c for c in X.columns if c not in self.cols_to_drop]
        return X[cols_to_keep]

    def get_feature_names_out(self, input_features=None):
        if input_features is None:
            input_features = self.feature_names_in_
        return [c for c in input_features if c not in self.cols_to_drop]

def load_features() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load graph metrics and compute decline label.
    Returns X (features), y (decline label: 1 if drop >= 3 points).
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {DATA_PATH}")
    
    df = pd.read_csv(DATA_PATH)
    
    # Ensure we have necessary columns
    required_cols = ['subject_id', 'mmse_baseline', 'mmse_followup']
    if not all(col in df.columns for col in required_cols):
        # Try to infer from available columns or raise error
        available = list(df.columns)
        raise ValueError(f"Missing required columns. Found: {available}, Required: {required_cols}")
    
    # Compute decline
    df['decline'] = df['mmse_baseline'] - df['mmse_followup']
    df['label'] = (df['decline'] >= DECLINE_THRESHOLD).astype(int)
    
    # Feature columns (exclude subject_id, labels, and score columns)
    feature_cols = [c for c in df.columns if c not in ['subject_id', 'mmse_baseline', 'mmse_followup', 'decline', 'label']]
    
    if not feature_cols:
        raise ValueError("No feature columns found in graph_metrics.csv")
    
    X = df[feature_cols].fillna(0)
    y = df['label']
    
    logger.log("load_features", subjects=len(X), features=len(feature_cols), positive_samples=y.sum())
    return X, y

def train_single_fold(X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple[float, Dict[str, Any]]:
    """
    Train a single fold with nested feature selection and hyperparameter tuning.
    Returns (auc, cv_results_dict).
    """
    # 1. Collinearity check (inside inner CV loop conceptually, but done on train set)
    collinearity_pipe = CollinearityTransformer(threshold=CORRELATION_THRESHOLD)
    X_train_coll = collinearity_pipe.fit_transform(X_train)
    
    # 2. Variance Thresholding
    var_thresh = VarianceThreshold(threshold=VARIANCE_THRESHOLD)
    X_train_var = var_thresh.fit_transform(X_train_coll)
    X_test_var = var_thresh.transform(collinearity_pipe.transform(X_test))
    
    # Convert back to DataFrame if needed for RFE
    feature_names = collinearity_pipe.get_feature_names_out()
    if len(X_train_var.shape) == 1:
        X_train_var = X_train_var.reshape(-1, 1)
        X_test_var = X_test_var.reshape(-1, 1)
        feature_names = [feature_names[0]] if feature_names else ['feature_0']
    
    X_train_var_df = pd.DataFrame(X_train_var, columns=feature_names)
    X_test_var_df = pd.DataFrame(X_test_var, columns=feature_names)
    
    # 3. RFE to select <= MAX_FEATURES
    rf_base = RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=1)
    rfe = RFE(estimator=rf_base, n_features_to_select=min(MAX_FEATURES, X_train_var_df.shape[1]))
    X_train_rfe = rfe.fit_transform(X_train_var_df, y_train)
    X_test_rfe = rfe.transform(X_test_var_df)
    
    selected_features = [f for f, s in zip(X_train_var_df.columns, rfe.support_) if s]
    
    if len(selected_features) == 0:
        # Fallback if RFE selects nothing
        selected_features = list(X_train_var_df.columns)[:1]
        X_train_rfe = X_train_var_df[selected_features].values
        X_test_rfe = X_test_var_df[selected_features].values
    
    X_train_final = pd.DataFrame(X_train_rfe, columns=selected_features)
    X_test_final = pd.DataFrame(X_test_rfe, columns=selected_features)
    
    # 4. Grid Search with Inner CV
    param_grid = {
        'n_estimators': N_ESTIMATORS,
        'max_depth': MAX_DEPTH
    }
    
    rf = RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=1)
    
    inner_cv = KFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
    grid_search = GridSearchCV(
        rf, param_grid, cv=inner_cv, scoring='roc_auc', n_jobs=1
    )
    
    grid_search.fit(X_train_final, y_train)
    
    best_model = grid_search.best_estimator_
    
    # Evaluate on test set
    try:
        y_pred_proba = best_model.predict_proba(X_test_final)[:, 1]
        auc = roc_auc_score(y_test, y_pred_proba)
    except Exception:
        # Handle case with single class or other errors
        auc = 0.5
    
    cv_results_dict = {
        'best_params': grid_search.best_params_,
        'selected_features': selected_features,
        'auc': auc,
        'n_features_selected': len(selected_features),
        'collinearity_dropped': collinearity_pipe.cols_to_drop,
        'variance_dropped': [c for c in X_train_coll.columns if c not in X_train_var_df.columns]
    }
    
    return auc, cv_results_dict

def train_and_evaluate_nested_cv() -> Tuple[Any, List[Dict[str, Any]]]:
    """
    Main nested cross-validation loop.
    Returns (final_model, list_of_fold_results).
    """
    X, y = load_features()
    
    if y.nunique() < 2:
        raise ValueError("Cannot train model: only one class present in labels.")
    
    outer_cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    
    fold_results = []
    all_test_indices = []
    
    # We need to train a final model on all data after CV
    # But for nested CV, we record metrics per fold
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        logger.log("fold_start", fold=fold_idx, train_size=len(X_train), test_size=len(X_test))
        
        auc, fold_info = train_single_fold(X_train, y_train, X_test, y_test)
        fold_info['fold'] = fold_idx
        fold_info['auc'] = auc
        fold_results.append(fold_info)
        
        all_test_indices.extend(test_idx)
        logger.log("fold_end", fold=fold_idx, auc=auc)
    
    # Train final model on all data
    logger.log("training_final_model")
    final_auc, final_info = train_single_fold(X, y, X, y)
    final_model_params = final_info['best_params']
    
    # Re-train final model with best params on all data
    final_rf = RandomForestClassifier(
        **final_model_params,
        random_state=RANDOM_SEED,
        n_jobs=1
    )
    
    # We need to re-run the full pipeline on all data to get the final model
    # This is a simplification: in practice, we'd store the pipeline
    collinearity_pipe = CollinearityTransformer(threshold=CORRELATION_THRESHOLD)
    X_coll = collinearity_pipe.fit_transform(X)
    
    var_thresh = VarianceThreshold(threshold=VARIANCE_THRESHOLD)
    X_var = var_thresh.fit_transform(X_coll)
    
    feature_names = collinearity_pipe.get_feature_names_out()
    if len(X_var.shape) == 1:
        X_var = X_var.reshape(-1, 1)
        feature_names = [feature_names[0]] if feature_names else ['feature_0']
    
    X_var_df = pd.DataFrame(X_var, columns=feature_names)
    
    rf_base = RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=1)
    rfe = RFE(estimator=rf_base, n_features_to_select=min(MAX_FEATURES, X_var_df.shape[1]))
    X_rfe = rfe.fit_transform(X_var_df, y)
    
    selected_features = [f for f, s in zip(X_var_df.columns, rfe.support_) if s]
    if not selected_features:
        selected_features = list(X_var_df.columns)[:1]
        X_rfe = X_var_df[selected_features].values
    
    X_final = pd.DataFrame(X_rfe, columns=selected_features)
    
    final_rf.fit(X_final, y)
    
    # Attach pipeline info to model for later use
    final_rf.pipeline_info = {
        'collinearity_dropped': collinearity_pipe.cols_to_drop,
        'variance_dropped': [c for c in X.columns if c not in X_var_df.columns],
        'selected_features': selected_features,
        'rfe_support': rfe.support_.tolist() if hasattr(rfe, 'support_') else []
    }
    
    logger.log("final_model_trained", n_features=len(selected_features))
    
    return final_rf, fold_results

def persist_model(model: Any):
    """Save the trained model to disk."""
    ensure_dir(MODEL_PATH.parent)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    logger.log("model_saved", path=str(MODEL_PATH))

def write_cv_results(results: List[Dict[str, Any]]):
    """Write CV results to JSON."""
    ensure_dir(CV_RESULTS_PATH.parent)
    output = {
        'fold_results': results,
        'mean_auc': np.mean([r['auc'] for r in results]),
        'std_auc': np.std([r['auc'] for r in results]),
        'n_folds': len(results),
        'grid_search_params': {'n_estimators': N_ESTIMATORS, 'max_depth': MAX_DEPTH}
    }
    save_json(output, CV_RESULTS_PATH)
    logger.log("cv_results_saved", path=str(CV_RESULTS_PATH), mean_auc=output['mean_auc'])

def write_model_params(model: Any):
    """Write model parameters to JSON."""
    ensure_dir(MODEL_PARAMS_PATH.parent)
    output = {
        'best_params': {
            'n_estimators': model.n_estimators,
            'max_depth': model.max_depth
        },
        'selected_features': model.pipeline_info.get('selected_features', []),
        'collinearity_dropped': model.pipeline_info.get('collinearity_dropped', []),
        'variance_dropped': model.pipeline_info.get('variance_dropped', []),
        'decline_threshold': DECLINE_THRESHOLD,
        'random_seed': RANDOM_SEED
    }
    save_json(output, MODEL_PARAMS_PATH)
    logger.log("model_params_saved", path=str(MODEL_PARAMS_PATH))

@log_operation("train_model_main")
def main():
    """Main entry point."""
    start_time = time.time()
    logger.log("start")
    
    try:
        model, fold_results = train_and_evaluate_nested_cv()
        persist_model(model)
        write_cv_results(fold_results)
        write_model_params(model)
        
        elapsed = time.time() - start_time
        logger.log("finish", elapsed_seconds=elapsed)
        print(f"Training completed in {elapsed:.2f} seconds.")
        print(f"Mean AUC: {np.mean([r['auc'] for r in fold_results]):.4f} (+/- {np.std([r['auc'] for r in fold_results]):.4f})")
        
    except Exception as e:
        logger.log("error", message=str(e))
        print(f"Error during training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()