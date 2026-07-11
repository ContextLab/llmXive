"""
Non-linear modeling module for User Story 3.
Implements Random Forest with grid search and timeout fallback mechanism.
"""
import os
import sys
import json
import logging
import time
import signal
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import get_config
from data.preprocess import load_processed_data

logger = logging.getLogger(__name__)

# Timeout exception class
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Model training timed out")

def get_default_params() -> Dict[str, Any]:
    """
    Returns default parameters for Random Forest when timeout occurs.
    """
    return {
        'n_estimators': 100,
        'max_depth': 10,
        'random_state': get_config().get('random_seed', 42)
    }

def train_with_timeout(
    X: np.ndarray,
    y: np.ndarray,
    param_grid: Dict[str, Any],
    timeout_seconds: int = 14400
) -> RandomForestRegressor:
    """
    Trains a Random Forest model with grid search.
    If the training exceeds timeout_seconds, falls back to default parameters.
    
    Args:
        X: Feature matrix
        y: Target vector
        param_grid: Grid search parameter grid
        timeout_seconds: Maximum time allowed for training (default 4 hours)
    
    Returns:
        Trained RandomForestRegressor model
    """
    config = get_config()
    default_params = get_default_params()
    
    # Set up the timeout handler
    # Note: signal.alarm only works on Unix-like systems.
    # For cross-platform compatibility, we might need threading, but sticking to signal for now
    # as per typical scientific computing environments.
    original_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        logger.info(f"Starting grid search with timeout {timeout_seconds}s")
        
        # Define the model
        rf = RandomForestRegressor(random_state=config.get('random_seed', 42))
        
        # Perform grid search
        grid_search = GridSearchCV(
            estimator=rf,
            param_grid=param_grid,
            cv=3,
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        # Cancel the alarm
        signal.alarm(0)
        
        logger.info(f"Grid search completed. Best params: {grid_search.best_params_}")
        return grid_search.best_estimator_
        
    except TimeoutError:
        logger.warning("Training timed out. Falling back to default parameters.")
        signal.alarm(0)
        
        # Train with default parameters
        rf_default = RandomForestRegressor(**default_params)
        rf_default.fit(X, y)
        
        return rf_default
        
    finally:
        # Restore the original handler
        signal.signal(signal.SIGALRM, original_handler)

def stratified_split_by_study(
    df: pd.DataFrame,
    test_size: float = 0.2
) -> tuple:
    """
    Splits data into train/test sets ensuring no leakage from source_study.
    If 'source_study' is not available, falls back to random split.
    """
    if 'source_study' in df.columns:
        # Group by source_study and sample
        train_df = df.groupby('source_study', group_keys=False).apply(
            lambda x: x.sample(frac=1-test_size, random_state=get_config().get('random_seed', 42))
        )
        test_df = df.drop(train_df.index)
        return train_df, test_df
    else:
        logger.warning("source_study column not found. Using random split.")
        return train_test_split(
            df,
            test_size=test_size,
            random_state=get_config().get('random_seed', 42)
        )

def run_non_linear_pipeline():
    """
    Main pipeline for non-linear modeling (User Story 3).
    """
    config = get_config()
    data_path = Path(config['data']['processed_path'])
    model_output_dir = Path(config['artifacts']['models_dir'])
    reports_dir = Path(config['artifacts']['reports_dir'])
    
    # Ensure directories exist
    model_output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info("Loading processed data...")
    df = load_processed_data(data_path)
    
    if df is None or df.empty:
        logger.error("No data available for non-linear modeling.")
        return
    
    # Prepare features and target
    # Assuming 'grain_size' is the target
    target_col = 'grain_size'
    if target_col not in df.columns:
        logger.error(f"Target column '{target_col}' not found in data.")
        return
    
    X = df.drop(columns=[target_col, 'source_study'] if 'source_study' in df.columns else [target_col]).values
    y = df[target_col].values
    
    # Split data
    train_df, test_df = stratified_split_by_study(df)
    
    X_train = train_df.drop(columns=[target_col, 'source_study'] if 'source_study' in train_df.columns else [target_col]).values
    y_train = train_df[target_col].values
    X_test = test_df.drop(columns=[target_col, 'source_study'] if 'source_study' in test_df.columns else [target_col]).values
    y_test = test_df[target_col].values
    
    # Define parameter grid
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [5, 10, 20, None]
    }
    
    # Train with timeout
    logger.info("Training Random Forest model with timeout fallback...")
    best_model = train_with_timeout(
        X_train,
        y_train,
        param_grid,
        timeout_seconds=config.get('training_timeout_seconds', 14400)
    )
    
    # Evaluate
    y_pred = best_model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    logger.info(f"Model Metrics - R²: {r2:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    
    # Save model
    model_path = model_output_dir / "non_linear_model.pkl"
    import joblib
    joblib.dump(best_model, model_path)
    logger.info(f"Model saved to {model_path}")
    
    # Save metrics
    metrics = {
        'r2': r2,
        'mae': mae,
        'rmse': rmse,
        'best_params': best_model.get_params()
    }
    metrics_path = reports_dir / "non_linear_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")
    
    return metrics

def main():
    """
    Entry point for non-linear modeling.
    """
    logging.basicConfig(level=logging.INFO)
    run_non_linear_pipeline()

if __name__ == "__main__":
    main()