"""
Train tuning script for XGBoost hyperparameter optimization.

This script performs a 70/15/15 train/validation/test split, executes
RandomizedSearchCV for hyperparameter tuning on the training set,
and saves the best hyperparameters and compute metrics.
"""
import json
import logging
import os
import sys
import time
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
import psutil
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from scipy.stats import uniform, randint

# Import from project modules
from utils import setup_logging, set_random_seed
from preprocess import load_parsed_data
from error_handling import DataInsufficiencyError, raise_data_insufficiency_error

# Setup logging
logger = setup_logging("train_tuning")

# Constants
RANDOM_SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15
CV_FOLDS = 5
N_ITERATIONS = 50  # Number of parameter settings sampled in RandomizedSearchCV
N_JOBS = 2  # Match CPU core constraint

# Hyperparameter search space
PARAM_DISTRIBUTION = {
    'max_depth': randint(3, 10),
    'learning_rate': uniform(0.01, 0.29),  # 0.01 to 0.30
    'n_estimators': randint(50, 250),      # 50 to 300
    'subsample': uniform(0.6, 0.4),        # 0.6 to 1.0
    'colsample_bytree': uniform(0.6, 0.4), # 0.6 to 1.0
}

def load_and_prepare_data() -> Tuple[pd.DataFrame, list]:
    """
    Load cleaned dataset and prepare features/target.
    
    Returns:
        Tuple of (features DataFrame, target column name)
    """
    logger.info("Loading cleaned dataset...")
    df = load_parsed_data("data/processed/cleaned_dataset.parquet")
    
    if df is None or df.empty:
        logger.error("Failed to load cleaned dataset. Ensure T011 has run successfully.")
        raise DataInsufficiencyError("Cleaned dataset is empty or missing.")
    
    logger.info(f"Loaded dataset with {len(df)} records.")
    
    # Define target and features based on project data model
    target_col = 'diffusivity'
    if target_col not in df.columns:
        logger.error(f"Target column '{target_col}' not found in dataset.")
        raise ValueError(f"Target column '{target_col}' missing from dataset.")
    
    # Select feature columns (exclude target and non-feature metadata)
    exclude_cols = [target_col, 'id', 'source', 'potential_id', 'simulation_method']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Handle case where no features remain
    if not feature_cols:
        logger.error("No feature columns available after filtering.")
        raise ValueError("No feature columns found in dataset.")
    
    logger.info(f"Using {len(feature_cols)} features: {feature_cols[:5]}...")
    
    return df[feature_cols], target_col

def split_data(X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Split data into train (70%), validation (15%), and test (15%) sets.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        
    Returns:
        Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    logger.info("Splitting data into train (70%), validation (15%), and test (15%) sets...")
    
    # First split: 70% train, 30% temp (val + test)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=(VAL_RATIO + TEST_RATIO), random_state=RANDOM_SEED
    )
    
    # Second split: 50% of temp for val, 50% for test (to get 15% each of total)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=RANDOM_SEED
    )
    
    logger.info(f"Train size: {len(X_train)}, Val size: {len(X_val)}, Test size: {len(X_test)}")
    
    # Save split indices for reproducibility in T012b
    split_indices = {
        'train': X_train.index.tolist(),
        'val': X_val.index.tolist(),
        'test': X_test.index.tolist()
    }
    output_path = Path("data/processed/split_indices.pkl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(split_indices, f)
    logger.info(f"Saved split indices to {output_path}")
    
    return X_train, X_val, X_test, y_train, y_val, y_test

def tune_hyperparameters(X_train: pd.DataFrame, y_train: pd.Series) -> Dict[str, Any]:
    """
    Perform RandomizedSearchCV for hyperparameter tuning.
    
    Args:
        X_train: Training features
        y_train: Training target
        
    Returns:
        Dictionary of best hyperparameters
    """
    logger.info("Starting hyperparameter tuning with RandomizedSearchCV...")
    
    base_model = XGBRegressor(
        objective='reg:squarederror',
        random_state=RANDOM_SEED,
        n_jobs=N_JOBS,
        verbosity=0
    )
    
    search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=PARAM_DISTRIBUTION,
        n_iter=N_ITERATIONS,
        scoring='r2',
        cv=CV_FOLDS,
        verbose=1,
        random_state=RANDOM_SEED,
        n_jobs=N_JOBS
    )
    
    search.fit(X_train, y_train)
    
    best_params = search.best_params_
    best_score = search.best_score_
    
    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best CV R² score: {best_score:.4f}")
    
    # Save best hyperparameters
    output_path = Path("models/best_params.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(best_params, f, indent=2)
    logger.info(f"Saved best hyperparameters to {output_path}")
    
    return best_params

def measure_compute_metrics(start_time: float, best_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Measure and log peak RAM usage and total runtime.
    
    Args:
        start_time: Start timestamp of the script
        best_params: Best hyperparameters found
        
    Returns:
        Dictionary of compute metrics
    """
    end_time = time.time()
    runtime_seconds = end_time - start_time
    
    # Get peak memory usage
    process = psutil.Process(os.getpid())
    peak_memory_mb = process.memory_info().rss / (1024 * 1024)
    
    compute_metrics = {
        "peak_memory_mb": round(peak_memory_mb, 2),
        "runtime_seconds": round(runtime_seconds, 2),
        "best_hyperparameters": best_params
    }
    
    # Save compute metrics
    output_path = Path("artifacts/reports/compute_metrics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(compute_metrics, f, indent=2)
    logger.info(f"Saved compute metrics to {output_path}")
    
    return compute_metrics

def main():
    """Main entry point for the training tuning script."""
    logger.info("Starting hyperparameter tuning pipeline...")
    start_time = time.time()
    
    try:
        # Set random seed for reproducibility
        set_random_seed(RANDOM_SEED)
        
        # Load and prepare data
        X, target_col = load_and_prepare_data()
        y = X.pop(target_col)  # Remove target from features
        
        # Split data
        X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
        
        # Tune hyperparameters
        best_params = tune_hyperparameters(X_train, y_train)
        
        # Measure compute metrics
        compute_metrics = measure_compute_metrics(start_time, best_params)
        
        logger.info("Hyperparameter tuning completed successfully.")
        logger.info(f"Peak memory: {compute_metrics['peak_memory_mb']:.2f} MB")
        logger.info(f"Runtime: {compute_metrics['runtime_seconds']:.2f} seconds")
        
    except DataInsufficiencyError as e:
        logger.error(f"Data insufficiency error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during tuning: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()