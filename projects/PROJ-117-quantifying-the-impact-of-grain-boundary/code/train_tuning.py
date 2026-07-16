"""
Train and tune XGBoost model for grain boundary diffusivity prediction.

This script performs a 70/15/15 train/validation/test split, executes
RandomizedSearchCV for hyperparameter tuning on the training set, and
saves the best hyperparameters and compute metrics.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
import psutil
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from xgboost import XGBRegressor

# Import from project utils
from utils import setup_logging, set_random_seed
from preprocess import load_parsed_data

# Configure logging
logger = setup_logging("train_tuning")

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
REPORTS_DIR = ARTIFACTS_DIR / "reports"

INPUT_FILE = PROCESSED_DIR / "cleaned_dataset.parquet"
SPLIT_INDICES_FILE = PROCESSED_DIR / "split_indices.pkl"
BEST_PARAMS_FILE = MODELS_DIR / "best_params.json"
COMPUTE_METRICS_FILE = REPORTS_DIR / "compute_metrics.json"

# Hyperparameter search space
PARAM_DISTRIBUTION = {
    'max_depth': [3, 4, 5, 6, 7, 8, 9, 10],
    'learning_rate': [0.01, 0.05, 0.1, 0.2, 0.3],
    'n_estimators': [50, 100, 150, 200, 250, 300]
}

def load_and_prepare_data() -> Tuple[pd.DataFrame, pd.Series]:
    """Load cleaned dataset and separate features from target."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")
    
    df = pd.read_parquet(INPUT_FILE)
    
    # Identify target column (assuming 'diffusivity' based on spec)
    target_col = 'diffusivity'
    if target_col not in df.columns:
        # Fallback: find column with 'diffusivity' in name
        matching_cols = [c for c in df.columns if 'diffusivity' in c.lower()]
        if matching_cols:
            target_col = matching_cols[0]
            logger.warning(f"Target column '{target_col}' found via fuzzy match.")
        else:
            raise ValueError(f"Target column '{target_col}' not found in dataset. Available columns: {list(df.columns)}")
    
    # Define features (exclude target and non-feature metadata if any)
    # Assuming all numeric columns except target are features
    feature_cols = [c for c in df.columns if c != target_col]
    
    X = df[feature_cols].dropna(axis=1)  # Drop columns with all NaN
    y = df[target_col]
    
    # Drop rows where target is NaN
    mask = y.notna()
    X = X[mask]
    y = y[mask]
    
    logger.info(f"Loaded {len(y)} records with {X.shape[1]} features.")
    return X, y

def split_data(X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Perform 70/15/15 train/validation/test split.
    Saves split indices to disk for reproducibility in T012b.
    """
    # First split: 70% train, 30% temp (for val+test)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42
    )
    
    # Second split: 50% of temp for validation, 50% for test (15% each of total)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42
    )
    
    # Save split indices for T012b
    split_indices = {
        'train': X_train.index.tolist(),
        'val': X_val.index.tolist(),
        'test': X_test.index.tolist()
    }
    SPLIT_INDICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    import pickle
    with open(SPLIT_INDICES_FILE, 'wb') as f:
        pickle.dump(split_indices, f)
    
    logger.info(f"Split saved: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
    return X_train, X_val, X_test, y_train, y_val, y_test

def tune_hyperparameters(X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series) -> Dict[str, Any]:
    """
    Execute RandomizedSearchCV for XGBoost hyperparameter tuning.
    """
    logger.info("Starting hyperparameter tuning...")
    
    # Initialize XGBoost regressor
    base_model = XGBRegressor(
        objective='reg:squarederror',
        random_state=42,
        n_jobs=-1,
        verbosity=0
    )
    
    # Perform RandomizedSearchCV
    search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=PARAM_DISTRIBUTION,
        n_iter=20,
        scoring='r2',
        cv=5,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    search.fit(X_train, y_train)
    
    best_params = search.best_params_
    best_score = search.best_score_
    
    logger.info(f"Best R² on validation: {best_score:.4f}")
    logger.info(f"Best hyperparameters: {best_params}")
    
    # Save best parameters
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(BEST_PARAMS_FILE, 'w') as f:
        json.dump(best_params, f, indent=2)
    
    return best_params

def measure_compute_metrics(start_time: float) -> Dict[str, Any]:
    """Measure peak RAM usage and total runtime."""
    end_time = time.time()
    process = psutil.Process(os.getpid())
    peak_memory_mb = process.memory_info().rss / (1024 * 1024)
    
    metrics = {
        'runtime_seconds': round(end_time - start_time, 2),
        'peak_memory_mb': round(peak_memory_mb, 2)
    }
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(COMPUTE_METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Runtime: {metrics['runtime_seconds']}s, Peak RAM: {metrics['peak_memory_mb']}MB")
    return metrics

def main():
    """Main entry point for training and tuning."""
    logger.info("Starting train_tuning pipeline...")
    start_time = time.time()
    
    try:
        # Load data
        X, y = load_and_prepare_data()
        
        # Split data
        X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
        
        # Tune hyperparameters
        best_params = tune_hyperparameters(X_train, y_train, X_val, y_val)
        
        # Measure and save compute metrics
        compute_metrics = measure_compute_metrics(start_time)
        
        logger.info("Train tuning completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during train tuning: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
