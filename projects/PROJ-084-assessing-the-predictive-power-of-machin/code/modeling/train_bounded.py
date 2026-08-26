"""
Bounded Training Pipeline for USPTO Reaction Prediction.

This module implements the training loop for Random Forest and SVM models
with strict memory constraints (<= 7GB RAM) and CPU-only execution.

It utilizes the memory utilities from `modeling.memory_utils` to:
1. Enforce CPU-only execution.
2. Validate input data size before processing.
3. Stream data in batches if necessary to stay within memory limits.
4. Force garbage collection between heavy operations.
"""

import gc
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Project imports
from config import RANDOM_SEED, DATA_PROCESSED_DIR, DATA_RESULTS_DIR
from modeling.memory_utils import (
    get_available_memory_gb,
    check_memory_limit,
    enforce_cpu_only,
    batch_dataframe,
    estimate_dataframe_memory_mb,
    validate_training_data_size,
    safe_gc
)
from modeling.split import extract_validation_set
from modeling.save_models import save_model_artifacts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_MEMORY_GB = 6.5  # Leave buffer for OS and Python overhead (7GB limit)
BATCH_SIZE_DEFAULT = 5000

def load_and_prepare_data(
    input_path: Path,
    split_path: Path,
    max_memory_gb: float = MAX_MEMORY_GB
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Loads data, validates size, and splits into train/test sets.
    If the dataset is too large for memory, it returns an iterator or 
    raises an error if batching logic isn't sufficient for the model.
    For RF/SVM, we attempt to load the full split if it fits, 
    otherwise we process in chunks to build the feature matrix.
    """
    logger.info(f"Loading data from {input_path}")
    
    # Check memory availability
    avail_mem = get_available_memory_gb()
    if avail_mem < max_memory_gb:
        logger.warning(f"Available memory ({avail_mem:.2f} GB) is below target ({max_memory_gb:.2f} GB). Proceeding with caution.")
    
    # Load split indices
    logger.info(f"Loading split indices from {split_path}")
    split_df = pd.read_parquet(split_path)
    
    # Extract validation set (held-out)
    # Note: T023 creates validation_set.parquet, but for training we need train/val indices
    # We assume split_indices.parquet has columns: 'index', 'split' (train, val, test)
    train_indices = split_df[split_df['split'] == 'train']['index'].values
    val_indices = split_df[split_df['split'] == 'val']['index'].values
    test_indices = split_df[split_df['split'] == 'test']['index'].values
    
    logger.info(f"Split sizes - Train: {len(train_indices)}, Val: {len(val_indices)}, Test: {len(test_indices)}")
    
    # Load full dataset to filter
    # If the file is too large, we might need to stream. 
    # For this implementation, we assume the cleaned parquet fits in memory 
    # or we use the memory_utils to check.
    logger.info("Loading cleaned reactions...")
    df = pd.read_parquet(input_path)
    
    # Estimate memory
    est_mem = estimate_dataframe_memory_mb(df)
    logger.info(f"Estimated data memory: {est_mem:.2f} MB")
    
    if est_mem > (max_memory_gb * 1024 * 0.8):
        logger.error(f"Data size ({est_mem:.2f} MB) exceeds 80% of memory limit. Cannot proceed safely.")
        raise MemoryError("Dataset too large for available memory.")
    
    # Filter for train and test sets
    # Note: We use 'val' as the validation set for hyperparameter tuning (GridSearchCV)
    # and 'test' as the final held-out set.
    train_df = df.iloc[train_indices].reset_index(drop=True)
    val_df = df.iloc[val_indices].reset_index(drop=True)
    test_df = df.iloc[test_indices].reset_index(drop=True)
    
    # Prepare features and targets
    # Assuming 'yield' is the target and 'fingerprint_ecfp4' is the feature column
    # The column name might vary, check config or data schema
    target_col = 'yield'
    feature_col = 'fingerprint_ecfp4' # Adjust based on actual data schema from T016
    
    X_train = np.array(list(train_df[feature_col]))
    y_train = train_df[target_col].values
    
    X_val = np.array(list(val_df[feature_col]))
    y_val = val_df[target_col].values
    
    X_test = np.array(list(test_df[feature_col]))
    y_test = test_df[target_col].values
    
    # Validate training data size
    validate_training_data_size(X_train, y_train, max_memory_gb)
    
    safe_gc()
    
    return X_train, y_train, X_val, y_val, X_test, y_test, train_df, val_df, test_df

def train_random_forest_bounded(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    param_grid: Optional[Dict[str, Any]] = None
) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """
    Trains a Random Forest model with GridSearchCV, ensuring CPU-only and memory safety.
    """
    logger.info("Starting Random Forest training with GridSearchCV...")
    
    if param_grid is None:
        param_grid = {
            'n_estimators': [50, 100],
            'max_depth': [10, 20, None],
            'min_samples_split': [2, 5],
            'n_jobs': [1]  # Force single thread for memory safety
        }
    
    rf = RandomForestRegressor(
        random_state=RANDOM_SEED,
        n_jobs=1,  # CPU-only, single process to control memory
        verbose=1
    )
    
    # Use KFold with shuffling=False to respect scaffold split order if needed,
    # but GridSearchCV usually shuffles internally unless specified.
    # We use n_splits=3 to reduce memory pressure during CV.
    cv = KFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
    
    grid_search = GridSearchCV(
        rf, 
        param_grid, 
        cv=cv, 
        scoring='r2', 
        n_jobs=1,  # Critical: prevent memory explosion from parallelism
        verbose=1
    )
    
    logger.info("Fitting GridSearchCV...")
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    logger.info(f"Best RF Parameters: {best_params}")
    logger.info(f"Best CV R2 Score: {grid_search.best_score_:.4f}")
    
    # Validate on validation set
    val_pred = best_model.predict(X_val)
    val_r2 = r2_score(y_val, val_pred)
    logger.info(f"Validation R2: {val_r2:.4f}")
    
    safe_gc()
    
    return best_model, best_params

def train_svm_bounded(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    param_grid: Optional[Dict[str, Any]] = None
) -> Tuple[SVR, Dict[str, Any]]:
    """
    Trains an SVM model with GridSearchCV, ensuring CPU-only and memory safety.
    Note: SVM can be memory intensive. We use a subset or chunked approach if needed.
    For now, we assume the data fits in memory after RF check.
    """
    logger.info("Starting SVM training with GridSearchCV...")
    
    if param_grid is None:
        param_grid = {
            'C': [0.1, 1.0],
            'kernel': ['linear', 'rbf'],
            'epsilon': [0.1, 0.2]
        }
    
    svm = SVR()
    
    cv = KFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)
    
    grid_search = GridSearchCV(
        svm,
        param_grid,
        cv=cv,
        scoring='r2',
        n_jobs=1, # Critical for memory
        verbose=1
    )
    
    logger.info("Fitting GridSearchCV...")
    try:
        grid_search.fit(X_train, y_train)
    except MemoryError:
        logger.error("SVM training ran out of memory. Consider reducing dataset size or parameters.")
        raise
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    logger.info(f"Best SVM Parameters: {best_params}")
    logger.info(f"Best CV R2 Score: {grid_search.best_score_:.4f}")
    
    val_pred = best_model.predict(X_val)
    val_r2 = r2_score(y_val, val_pred)
    logger.info(f"Validation R2: {val_r2:.4f}")
    
    safe_gc()
    
    return best_model, best_params

def main():
    """
    Main entry point for bounded training pipeline.
    """
    # 1. Enforce CPU-only
    enforce_cpu_only()
    
    # 2. Define paths
    input_path = DATA_PROCESSED_DIR / "cleaned_reactions.parquet"
    split_path = DATA_PROCESSED_DIR / "split_indices.parquet"
    results_dir = DATA_RESULTS_DIR / "best_models"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input data not found at {input_path}")
    if not split_path.exists():
        raise FileNotFoundError(f"Split indices not found at {split_path}")
    
    # 3. Load and prepare data with memory checks
    try:
        (X_train, y_train, X_val, y_val, X_test, y_test, 
         train_df, val_df, test_df) = load_and_prepare_data(input_path, split_path)
    except MemoryError as e:
        logger.critical(f"Data loading failed due to memory constraints: {e}")
        sys.exit(1)
    
    # 4. Train Random Forest
    rf_model, rf_params = train_random_forest_bounded(X_train, y_train, X_val, y_val)
    
    # 5. Train SVM
    svm_model, svm_params = train_svm_bounded(X_train, y_train, X_val, y_val)
    
    # 6. Evaluate on Test Set
    logger.info("Evaluating on Test Set...")
    
    # RF Test
    rf_test_pred = rf_model.predict(X_test)
    rf_test_r2 = r2_score(y_test, rf_test_pred)
    rf_test_rmse = np.sqrt(mean_squared_error(y_test, rf_test_pred))
    rf_test_mae = mean_absolute_error(y_test, rf_test_pred)
    logger.info(f"RF Test R2: {rf_test_r2:.4f}, RMSE: {rf_test_rmse:.4f}, MAE: {rf_test_mae:.4f}")
    
    # SVM Test
    svm_test_pred = svm_model.predict(X_test)
    svm_test_r2 = r2_score(y_test, svm_test_pred)
    svm_test_rmse = np.sqrt(mean_squared_error(y_test, svm_test_pred))
    svm_test_mae = mean_absolute_error(y_test, svm_test_pred)
    logger.info(f"SVM Test R2: {svm_test_r2:.4f}, RMSE: {svm_test_rmse:.4f}, MAE: {svm_test_mae:.4f}")
    
    # 7. Save Artifacts
    ensure_dir(results_dir)
    
    save_model_artifacts(
        models={
            'random_forest': rf_model,
            'svm': svm_model
        },
        params={
            'random_forest': rf_params,
            'svm': svm_params
        },
        metrics={
            'random_forest': {
                'test_r2': float(rf_test_r2),
                'test_rmse': float(rf_test_rmse),
                'test_mae': float(rf_test_mae)
            },
            'svm': {
                'test_r2': float(svm_test_r2),
                'test_rmse': float(svm_test_rmse),
                'test_mae': float(svm_test_mae)
            }
        },
        output_dir=results_dir
    )
    
    logger.info("Training pipeline completed successfully.")

if __name__ == "__main__":
    main()