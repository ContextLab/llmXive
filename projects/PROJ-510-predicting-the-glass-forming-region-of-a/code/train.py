"""
Model Training Module.

Handles splitting data, training Random Forest and Dummy models,
cross-validation, and statistical comparison.
"""
import logging
import os
import sys
import json
import pickle
import pandas as pd
from typing import List, Dict, Any
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
from utils import get_logger, ensure_dir

logger = get_logger(__name__)

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
DATA_MODELS_DIR = os.path.join(PROJECT_ROOT, 'data', 'models')
DATA_LOGS_DIR = os.path.join(PROJECT_ROOT, 'data', 'logs')

ensure_dir(DATA_PROCESSED_DIR)
ensure_dir(DATA_MODELS_DIR)
ensure_dir(DATA_LOGS_DIR)

INPUT_PATH = os.path.join(DATA_PROCESSED_DIR, 'processed_alloys.csv')
TRAIN_SET_PATH = os.path.join(DATA_PROCESSED_DIR, 'train_set.csv')
TEST_SET_PATH = os.path.join(DATA_PROCESSED_DIR, 'test_set.csv')
SPLIT_INDICES_PATH = os.path.join(DATA_MODELS_DIR, 'split_indices.json')
CV_METRICS_PATH = os.path.join(DATA_MODELS_DIR, 'cv_metrics.json')
CV_FOLDS_INDICES_PATH = os.path.join(DATA_MODELS_DIR, 'cv_folds_indices.json')
MODEL_PATH = os.path.join(DATA_MODELS_DIR, 'random_forest_model.pkl')
NULL_MODEL_PATH = os.path.join(DATA_MODELS_DIR, 'null_model.pkl')
NULL_CV_SCORES_PATH = os.path.join(DATA_MODELS_DIR, 'null_model_cv_scores.json')
NULL_PREDICTIONS_PATH = os.path.join(DATA_MODELS_DIR, 'null_model_predictions.npy')
NULL_RMSE_PATH = os.path.join(DATA_MODELS_DIR, 'null_model_rmse.json')
STAT_COMPARISON_PATH = os.path.join(DATA_MODELS_DIR, 'statistical_comparison.json')
SC002_STATUS_PATH = os.path.join(DATA_MODELS_DIR, 'sc002_status.json')
TRAINING_VALIDATION_PATH = os.path.join(DATA_LOGS_DIR, 'training_set_validation.json')

RANDOM_STATE = 42
TEST_SIZE = 0.2
N_SPLITS = 5

def load_data() -> pd.DataFrame:
    """Load the processed dataset."""
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")
    df = pd.read_csv(INPUT_PATH)
    
    # Validate size
    n_total = len(df)
    status = "pass" if n_total >= 500 else "fail"
    msg = "Data size sufficient." if status == "pass" else f"Data size < 500 (N={n_total})."
    
    validation = {"status": status, "n_total": n_total}
    with open(TRAINING_VALIDATION_PATH, 'w') as f:
        json.dump(validation, f, indent=2)
    
    if status == "fail":
        raise ValueError(msg)
    
    return df

def train_model(X, y):
    """Train a Random Forest Regressor."""
    model = RandomForestRegressor(
        n_estimators=100, 
        random_state=RANDOM_STATE, 
        n_jobs=-1
    )
    model.fit(X, y)
    return model

def run_cross_validation(model, X, y, kf: KFold) -> Dict[str, Any]:
    """Run k-fold cross-validation and save indices."""
    scores = []
    fold_indices = []
    
    # Convert to numpy for indexing
    X_np = X.values if isinstance(X, pd.DataFrame) else X
    y_np = y.values if isinstance(y, pd.Series) else y
    
    for train_idx, test_idx in kf.split(X_np):
        X_train_fold = X_np[train_idx]
        y_train_fold = y_np[train_idx]
        X_test_fold = X_np[test_idx]
        y_test_fold = y_np[test_idx]
        
        # Fit on fold
        fold_model = RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1)
        fold_model.fit(X_train_fold, y_train_fold)
        
        # Predict
        y_pred = fold_model.predict(X_test_fold)
        rmse = mean_squared_error(y_test_fold, y_pred, squared=False)
        scores.append(rmse)
        
        fold_indices.append({
            "train": train_idx.tolist(),
            "test": test_idx.tolist()
        })
    
    mean_rmse = sum(scores) / len(scores)
    std_rmse = (sum((s - mean_rmse)**2 for s in scores) / len(scores))**0.5
    
    return {
        "fold_scores": scores,
        "mean_rmse": mean_rmse,
        "std_rmse": std_rmse,
        "indices": fold_indices
    }

def evaluate_on_test(model, X_test, y_test) -> float:
    """Evaluate model on test set."""
    y_pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    return rmse

def save_model(model, path):
    """Save model to pickle."""
    with open(path, 'wb') as f:
        pickle.dump(model, f)

def train_and_evaluate_null_model(X_train, y_train, X_test, y_test, kf: KFold) -> Dict[str, Any]:
    """Train DummyRegressor and perform CV + Test evaluation."""
    # Train null model
    null_model = DummyRegressor(strategy='mean', random_state=RANDOM_STATE)
    null_model.fit(X_train, y_train)
    save_model(null_model, NULL_MODEL_PATH)
    
    # Cross Validation for Null Model
    scores = []
    X_np = X_train.values if isinstance(X_train, pd.DataFrame) else X_train
    y_np = y_train.values if isinstance(y_train, pd.Series) else y_train
    
    for train_idx, test_idx in kf.split(X_np):
        X_tr = X_np[train_idx]
        y_tr = y_np[train_idx]
        X_te = X_np[test_idx]
        y_te = y_np[test_idx]
        
        nm = DummyRegressor(strategy='mean', random_state=RANDOM_STATE)
        nm.fit(X_tr, y_tr)
        pred = nm.predict(X_te)
        rmse = mean_squared_error(y_te, pred, squared=False)
        scores.append(rmse)
    
    mean_rmse = sum(scores) / len(scores)
    std_rmse = (sum((s - mean_rmse)**2 for s in scores) / len(scores))**0.5
    
    null_cv_result = {
        "fold_scores": scores,
        "mean_rmse": mean_rmse,
        "std_rmse": std_rmse
    }
    
    with open(NULL_CV_SCORES_PATH, 'w') as f:
        json.dump(null_cv_result, f, indent=2)
    
    # Test set evaluation
    y_pred_null = null_model.predict(X_test)
    import numpy as np
    np.save(NULL_PREDICTIONS_PATH, y_pred_null)
    rmse_null = mean_squared_error(y_test, y_pred_null, squared=False)
    
    with open(NULL_RMSE_PATH, 'w') as f:
        json.dump({"test_rmse": rmse_null}, f, indent=2)
    
    return null_cv_result, rmse_null

def run_training() -> None:
    """Main entry point for training pipeline."""
    logger.info("Starting training pipeline.")
    
    # Load Data
    df = load_data()
    
    # Split Data
    from sklearn.model_selection import train_test_split
    feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    target_col = 'critical_cooling_rate'
    
    X = df[feature_cols]
    y = df[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    
    # Save splits
    train_indices = X_train.index.tolist()
    test_indices = X_test.index.tolist()
    
    with open(SPLIT_INDICES_PATH, 'w') as f:
        json.dump({"train": train_indices, "test": test_indices}, f, indent=2)
    
    X_train.to_csv(TRAIN_SET_PATH, index=False)
    X_test.to_csv(TEST_SET_PATH, index=False)
    y_train.to_csv(os.path.join(DATA_PROCESSED_DIR, 'train_target.csv'), index=False)
    y_test.to_csv(os.path.join(DATA_PROCESSED_DIR, 'test_target.csv'), index=False)
    
    # KFold
    kf = KFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    
    # Train RF
    rf_model = train_model(X_train, y_train)
    save_model(rf_model, MODEL_PATH)
    
    # CV
    cv_results = run_cross_validation(rf_model, X_train, y_train, kf)
    
    with open(CV_METRICS_PATH, 'w') as f:
        json.dump({
            "fold_scores": cv_results["fold_scores"],
            "mean_rmse": cv_results["mean_rmse"],
            "std_rmse": cv_results["std_rmse"]
        }, f, indent=2)
    
    with open(CV_FOLDS_INDICES_PATH, 'w') as f:
        json.dump(cv_results["indices"], f, indent=2)
    
    # Null Model
    null_cv_res, null_test_rmse = train_and_evaluate_null_model(X_train, y_train, X_test, y_test, kf)
    
    # Statistical Test
    rf_scores = cv_results["fold_scores"]
    null_scores = null_cv_res["fold_scores"]
    
    t_stat, p_value = ttest_rel(rf_scores, null_scores)
    
    sc002_met = p_value < 0.05
    
    stat_res = {
        "p_value": float(p_value),
        "t_statistic": float(t_stat),
        "sc002_met": bool(sc002_met)
    }
    
    with open(STAT_COMPARISON_PATH, 'w') as f:
        json.dump(stat_res, f, indent=2)
    
    # Gate Status
    sc002_status = "PASSED" if sc002_met else "FAILED"
    with open(SC002_STATUS_PATH, 'w') as f:
        json.dump({"sc002_status": sc002_status}, f, indent=2)
    
    if not sc002_met:
        logger.warning("SC-002 failed: Model not statistically distinguishable from null.")
    
    logger.info("Training pipeline completed.")

if __name__ == "__main__":
    run_training()
