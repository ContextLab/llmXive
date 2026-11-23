"""
Training module for Glass Forming Region prediction.
Implements model training, cross-validation, and evaluation.
"""
import logging
import os
import sys
import json
import pickle
import pandas as pd
from typing import Tuple, Dict, Any, List
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_squared_error
import numpy as np

from utils import get_logger, ensure_dir

logger = get_logger(__name__)

# Paths
PROCESSED_DATA_PATH = "data/processed/processed_alloys.csv"
TRAIN_SET_PATH = "data/processed/train_set.csv"
TEST_SET_PATH = "data/processed/test_set.csv"
SPLIT_INDICES_PATH = "data/models/split_indices.json"
MODEL_PATH = "data/models/random_forest_model.pkl"
CV_METRICS_PATH = "data/models/cv_metrics.json"
CV_FOLDS_INDICES_PATH = "data/models/cv_folds_indices.json"
NULL_MODEL_PATH = "data/models/null_model.pkl"
NULL_MODEL_CV_SCORES_PATH = "data/models/null_model_cv_scores.json"
NULL_MODEL_PREDICTIONS_PATH = "data/models/null_model_predictions.npy"
NULL_MODEL_RMSE_PATH = "data/models/null_model_rmse.json"
TRAINING_VALIDATION_PATH = "data/logs/training_set_validation.json"
SC002_STATUS_PATH = "data/models/sc002_status.json"
STATISTICAL_COMPARISON_PATH = "data/models/statistical_comparison.json"
TEST_METRICS_PATH = "data/models/test_metrics.json"

RANDOM_STATE = 42
TEST_SIZE = 0.2
N_SPLITS = 5

def load_data() -> pd.DataFrame:
    """Load the processed alloys dataset."""
    if not os.path.exists(PROCESSED_DATA_PATH):
        raise FileNotFoundError(f"Input file not found: {PROCESSED_DATA_PATH}. Run features.py first.")
    logger.info(f"Loading data from {PROCESSED_DATA_PATH}")
    df = pd.read_csv(PROCESSED_DATA_PATH)
    
    # Validate dataset size before splitting (T019 / SC-001)
    n_total = len(df)
    status = "pass" if n_total >= 500 else "fail"
    message = "Dataset size sufficient" if n_total >= 500 else "Dataset size below minimum (N < 500)"
    
    validation_result = {
        "status": status,
        "n_total": n_total
    }
    
    ensure_dir(TRAINING_VALIDATION_PATH)
    with open(TRAINING_VALIDATION_PATH, 'w') as f:
        json.dump(validation_result, f, indent=2)
    
    logger.info(f"Validation status: {status}, N={n_total}")
    if n_total < 500:
        raise ValueError(f"SC-001 Violation: Total dataset size < 500. Minimum N >= 500 required by FR-001.")
    
    return df

def train_model(X: pd.DataFrame, y: pd.Series) -> RandomForestRegressor:
    """Train a Random Forest regressor."""
    logger.info("Training Random Forest model...")
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    model.fit(X, y)
    return model

def run_cross_validation(model: RandomForestRegressor, X: pd.DataFrame, y: pd.Series) -> Tuple[List[float], Dict[str, Any]]:
    """Perform 5-fold cross-validation and save indices."""
    logger.info("Performing 5-fold cross-validation...")
    kfold = KFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    
    scores = []
    fold_indices = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(kfold.split(X)):
        X_train_fold, X_test_fold = X.iloc[train_idx], X.iloc[test_idx]
        y_train_fold, y_test_fold = y.iloc[train_idx], y.iloc[test_idx]
        
        # Train on fold
        fold_model = train_model(X_train_fold, y_train_fold)
        y_pred = fold_model.predict(X_test_fold)
        rmse = np.sqrt(mean_squared_error(y_test_fold, y_pred))
        scores.append(rmse)
        
        # Store indices for reproducibility
        fold_indices.append({
            "train": train_idx.tolist(),
            "test": test_idx.tolist()
        })
        
        logger.info(f"Fold {fold_idx + 1}/{N_SPLITS}: RMSE = {rmse:.4f}")
    
    mean_rmse = np.mean(scores)
    std_rmse = np.std(scores)
    
    cv_metrics = {
        "fold_scores": scores,
        "mean_rmse": float(mean_rmse),
        "std_rmse": float(std_rmse)
    }
    
    # Save CV metrics
    ensure_dir(CV_METRICS_PATH)
    with open(CV_METRICS_PATH, 'w') as f:
        json.dump(cv_metrics, f, indent=2)
    
    # Save fold indices (T021 requirement)
    ensure_dir(CV_FOLDS_INDICES_PATH)
    with open(CV_FOLDS_INDICES_PATH, 'w') as f:
        json.dump(fold_indices, f, indent=2)
    
    logger.info(f"Cross-validation complete. Mean RMSE: {mean_rmse:.4f}, Std: {std_rmse:.4f}")
    return scores, cv_metrics

def evaluate_on_test(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> float:
    """Evaluate model on the test set."""
    logger.info("Evaluating on test set...")
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    logger.info(f"Test RMSE: {rmse:.4f}")
    
    test_metrics = {"test_rmse": float(rmse)}
    ensure_dir(TEST_METRICS_PATH)
    with open(TEST_METRICS_PATH, 'w') as f:
        json.dump(test_metrics, f, indent=2)
        
    return rmse

def save_model(model: RandomForestRegressor, path: str = MODEL_PATH):
    """Save the trained model to disk."""
    ensure_dir(path)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {path}")

def train_and_evaluate_null_model(X_train: pd.DataFrame, y_train: pd.Series, 
                                  X_test: pd.DataFrame, y_test: pd.Series,
                                  fold_indices: List[Dict]) -> None:
    """Train a DummyRegressor (null model) and perform CV using the same splits."""
    logger.info("Training Null Model (DummyRegressor)...")
    
    # 1. Train on full training set
    null_model = DummyRegressor(strategy='mean')
    null_model.fit(X_train, y_train)
    
    # Save null model
    ensure_dir(NULL_MODEL_PATH)
    with open(NULL_MODEL_PATH, 'wb') as f:
        pickle.dump(null_model, f)
    
    # 2. Cross-validation using the SAME folds as the real model
    logger.info("Performing 5-fold CV on Null Model using shared splits...")
    fold_scores = []
    
    for fold_data in fold_indices:
        train_idx = fold_data['train']
        test_idx = fold_data['test']
        
        X_tr, X_te = X_train.iloc[train_idx], X_train.iloc[test_idx]
        y_tr, y_te = y_train.iloc[train_idx], y_train.iloc[test_idx]
        
        # Retrain dummy on this fold's train set (to simulate proper CV)
        fold_null = DummyRegressor(strategy='mean')
        fold_null.fit(X_tr, y_tr)
        
        y_pred = fold_null.predict(X_te)
        rmse = np.sqrt(mean_squared_error(y_te, y_pred))
        fold_scores.append(rmse)
    
    mean_rmse = np.mean(fold_scores)
    std_rmse = np.std(fold_scores)
    
    null_cv_metrics = {
        "fold_scores": fold_scores,
        "mean_rmse": float(mean_rmse),
        "std_rmse": float(std_rmse)
    }
    
    ensure_dir(NULL_MODEL_CV_SCORES_PATH)
    with open(NULL_MODEL_CV_SCORES_PATH, 'w') as f:
        json.dump(null_cv_metrics, f, indent=2)
    
    # 3. Evaluate on Test Set
    y_pred_test = null_model.predict(X_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    
    # Save predictions
    ensure_dir(NULL_MODEL_PREDICTIONS_PATH)
    np.save(NULL_MODEL_PREDICTIONS_PATH, y_pred_test)
    
    # Save test RMSE
    null_test_metrics = {"test_rmse": float(test_rmse)}
    ensure_dir(NULL_MODEL_RMSE_PATH)
    with open(NULL_MODEL_RMSE_PATH, 'w') as f:
        json.dump(null_test_metrics, f, indent=2)
    
    logger.info(f"Null Model CV Mean RMSE: {mean_rmse:.4f}, Test RMSE: {test_rmse:.4f}")
    
    # 4. Statistical Comparison (T024a)
    logger.info("Performing paired t-test (SC-002)...")
    from scipy.stats import ttest_rel
    
    # Load real model CV scores (already computed in run_cross_validation)
    with open(CV_METRICS_PATH, 'r') as f:
        real_cv_data = json.load(f)
    real_scores = real_cv_data['fold_scores']
    
    t_stat, p_value = ttest_rel(real_scores, fold_scores)
    
    sc002_met = p_value < 0.05
    
    stat_comparison = {
        "p_value": float(p_value),
        "t_statistic": float(t_stat),
        "sc002_met": bool(sc002_met)
    }
    
    ensure_dir(STATISTICAL_COMPARISON_PATH)
    with open(STATISTICAL_COMPARISON_PATH, 'w') as f:
        json.dump(stat_comparison, f, indent=2)
    
    # 5. Gate Status (T024c)
    sc002_status = {
        "sc002_status": "PASSED" if sc002_met else "FAILED"
    }
    ensure_dir(SC002_STATUS_PATH)
    with open(SC002_STATUS_PATH, 'w') as f:
        json.dump(sc002_status, f, indent=2)
        
    if not sc002_met:
        logger.warning("SC-002 failed: Model not statistically distinguishable from null.")
    else:
        logger.info("SC-002 passed: Model is statistically better than null.")

def run_training():
    """Main entry point for the training pipeline."""
    logger.info("Starting training pipeline...")
    
    # Load data
    df = load_data()
    
    # Define features and target
    # Assuming these columns exist based on previous tasks
    feature_cols = [
        'mixing_enthalpy', 
        'atomic_size_mismatch', 
        'electronegativity_variance',
        # Add other engineered features if present, but we rely on the schema
    ]
    # Dynamically identify feature columns if not hardcoded, 
    # but for now we assume the schema columns are present.
    # We will use all numeric columns except target and known metadata.
    target_col = 'critical_cooling_rate'
    
    # Filter columns to ensure we have features
    available_features = [c for c in feature_cols if c in df.columns]
    if not available_features:
        # Fallback: use all numeric columns except target
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        available_features = [c for c in numeric_cols if c != target_col]
    
    logger.info(f"Using features: {available_features}")
    
    X = df[available_features]
    y = df[target_col]
    
    # Check variance
    if y.var() == 0:
        raise ValueError("Target variable has zero variance; cannot train regression model.")
    
    # T020: Train-Test Split
    logger.info("Performing train-test split (T020)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    
    # Save splits
    ensure_dir(TRAIN_SET_PATH)
    ensure_dir(TEST_SET_PATH)
    
    train_df = pd.concat([X_train, y_train], axis=1)
    test_df = pd.concat([X_test, y_test], axis=1)
    
    train_df.to_csv(TRAIN_SET_PATH, index=False)
    test_df.to_csv(TEST_SET_PATH, index=False)
    
    # Save split indices
    split_indices = {
        "train_indices": X_train.index.tolist(),
        "test_indices": X_test.index.tolist()
    }
    ensure_dir(SPLIT_INDICES_PATH)
    with open(SPLIT_INDICES_PATH, 'w') as f:
        json.dump(split_indices, f, indent=2)
    
    logger.info(f"Split complete. Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Train Model
    model = train_model(X_train, y_train)
    
    # Cross-Validation (T021)
    cv_scores, cv_metrics = run_cross_validation(model, X_train, y_train)
    
    # Save Model
    save_model(model)
    
    # Evaluate on Test
    test_rmse = evaluate_on_test(model, X_test, y_test)
    
    # Train and Evaluate Null Model (T022b-1, T022b-2c, T022b-3, T024a, T024c)
    # Pass the fold indices from CV to ensure identical splits
    with open(CV_FOLDS_INDICES_PATH, 'r') as f:
        fold_indices = json.load(f)
    train_and_evaluate_null_model(X_train, y_train, X_test, y_test, fold_indices)
    
    logger.info("Training pipeline completed successfully.")

if __name__ == "__main__":
    run_training()