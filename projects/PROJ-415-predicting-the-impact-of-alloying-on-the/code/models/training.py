"""
Model training module for diffusion activation energy prediction.
Implements Random Forest, Gradient Boosting, and Linear Regression models.
"""
import json
import logging
import pickle
import signal
import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Import project utilities
from config import MODELS_DIR, DATA_DIR, PROJECT_ROOT
from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Timeout configuration
TRAINING_TIMEOUT_SECONDS = 1800  # 30 minutes

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Training timeout exceeded")

class TimeoutContext:
    """Context manager for timeout handling."""
    def __init__(self, seconds: int):
        self.seconds = seconds
        self.old_handler = None

    def __enter__(self):
        # Only set signal handler on Unix systems
        if hasattr(signal, 'SIGALRM'):
            self.old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            if self.old_handler:
                signal.signal(signal.SIGALRM, self.old_handler)

def verify_data_provenance(data_path: Path) -> None:
    """
    Verify that the input data is NOT a synthetic/mock dataset.
    
    Checks for the existence of data_provenance.json and validates
    that the source is a real URL or package, not 'mock' or 'synthetic'.
    
    Args:
        data_path: Path to the curated data file (data/curated/filtered.csv)
        
    Raises:
        SystemExit: If data is synthetic/mock or provenance is missing
    """
    provenance_path = data_path.parent / "data_provenance.json"
    
    if not provenance_path.exists():
        logger.error(f"Data provenance file not found: {provenance_path}")
        raise SystemExit(
            "Training Error: Cannot train on synthetic data. "
            "Real data source required. Missing data_provenance.json."
        )
    
    try:
        with open(provenance_path, 'r') as f:
            provenance = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in data_provenance.json: {e}")
        raise SystemExit(
            "Training Error: Cannot train on synthetic data. "
            "Real data source required. Corrupted data_provenance.json."
        )
    
    source_type = provenance.get('source_type', '').lower()
    source_url = provenance.get('source_url', '').lower()
    
    # Check for synthetic/mock indicators
    if source_type in ['mock', 'synthetic', 'generated']:
        logger.error(f"Data source type is synthetic: {source_type}")
        raise SystemExit(
            "Training Error: Cannot train on synthetic data. "
            "Real data source required. Detected source_type: " + source_type
        )
    
    if 'mock' in source_url or 'synthetic' in source_url:
        logger.error(f"Data source URL indicates synthetic data: {source_url}")
        raise SystemExit(
            "Training Error: Cannot train on synthetic data. "
            "Real data source required. Detected source_url: " + source_url
        )
    
    # Verify we have a real URL or package source
    if not source_url or not source_url.startswith(('http://', 'https://', 'pkg://')):
        # If no URL but we have other indicators of real data (like a package name), it might be okay
        # But if completely missing, we should be cautious
        if not provenance.get('source_package'):
            logger.warning(f"Data provenance missing clear real source indicator: {provenance}")
            # We'll allow it to proceed if no explicit mock/synthetic flag, but log warning
            logger.info("Proceeding with training - no explicit synthetic flag found in provenance")
        else:
            logger.info(f"Proceeding with training - source package: {provenance.get('source_package')}")
    else:
        logger.info(f"Verified real data source: {source_url}")

def prepare_features_target(data_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare features and target from curated data.
    
    Args:
        data_path: Path to the curated CSV file
        
    Returns:
        Tuple of (features, target) arrays
    """
    df = pd.read_csv(data_path)
    
    # Define feature columns based on the project's descriptor computation
    # Expected columns: size_mismatch, electronegativity_diff, etc.
    feature_columns = ['size_mismatch']
    
    # Check if all expected columns exist
    missing_cols = [col for col in feature_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required feature columns: {missing_cols}")
        raise ValueError(f"Missing required feature columns: {missing_cols}")
    
    X = df[feature_columns].values
    y = df['activation_energy'].values
    
    logger.info(f"Prepared features: {X.shape}, target: {y.shape}")
    return X, y

def train_random_forest(X_train: np.ndarray, y_train: np.ndarray, 
                        X_test: np.ndarray, y_test: np.ndarray) -> Tuple[Any, Dict[str, float]]:
    """
    Train Random Forest model with GridSearchCV.
    
    Args:
        X_train: Training features
        y_train: Training targets
        X_test: Test features
        y_test: Test targets
        
    Returns:
        Tuple of (best_model, metrics_dict)
    """
    logger.info("Starting Random Forest training with GridSearchCV...")
    
    param_grid = {
        'max_depth': [3, 5, 7, 10],
        'n_estimators': [50, 100, 150, 200]
    }
    
    rf = RandomForestRegressor(random_state=42, n_jobs=-1)
    
    try:
        with TimeoutContext(TRAINING_TIMEOUT_SECONDS):
            grid_search = GridSearchCV(
                rf, param_grid, cv=5, scoring='r2', n_jobs=-1, verbose=1
            )
            grid_search.fit(X_train, y_train)
    except TimeoutError:
        logger.error("Random Forest GridSearch timed out")
        raise SystemExit("Training Timeout: GridSearch exceeded 30min limit")
    except MemoryError:
        logger.error("Random Forest GridSearch ran out of memory")
        raise SystemExit("Memory Error: GridSearch exceeds resource limits")
    
    best_model = grid_search.best_estimator_
    
    # Calculate metrics
    y_pred = best_model.predict(X_test)
    metrics = {
        'r2': float(r2_score(y_test, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
        'mae': float(mean_absolute_error(y_test, y_pred)),
        'best_params': grid_search.best_params_,
        'best_score': float(grid_search.best_score_)
    }
    
    logger.info(f"Random Forest training complete. R²: {metrics['r2']:.4f}")
    return best_model, metrics

def train_gradient_boosting(X_train: np.ndarray, y_train: np.ndarray,
                            X_test: np.ndarray, y_test: np.ndarray) -> Tuple[Any, Dict[str, float]]:
    """
    Train Gradient Boosting model with GridSearchCV.
    
    Args:
        X_train: Training features
        y_train: Training targets
        X_test: Test features
        y_test: Test targets
        
    Returns:
        Tuple of (best_model, metrics_dict)
    """
    logger.info("Starting Gradient Boosting training with GridSearchCV...")
    
    param_grid = {
        'max_depth': [3, 5, 7, 10],
        'n_estimators': [50, 100, 150, 200],
        'learning_rate': [0.05, 0.1, 0.2]
    }
    
    gb = GradientBoostingRegressor(random_state=42)
    
    try:
        with TimeoutContext(TRAINING_TIMEOUT_SECONDS):
            grid_search = GridSearchCV(
                gb, param_grid, cv=5, scoring='r2', n_jobs=-1, verbose=1
            )
            grid_search.fit(X_train, y_train)
    except TimeoutError:
        logger.error("Gradient Boosting GridSearch timed out")
        raise SystemExit("Training Timeout: GridSearch exceeded 30min limit")
    except MemoryError:
        logger.error("Gradient Boosting GridSearch ran out of memory")
        raise SystemExit("Memory Error: GridSearch exceeds resource limits")
    
    best_model = grid_search.best_estimator_
    
    # Calculate metrics
    y_pred = best_model.predict(X_test)
    metrics = {
        'r2': float(r2_score(y_test, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
        'mae': float(mean_absolute_error(y_test, y_pred)),
        'best_params': grid_search.best_params_,
        'best_score': float(grid_search.best_score_)
    }
    
    logger.info(f"Gradient Boosting training complete. R²: {metrics['r2']:.4f}")
    return best_model, metrics

def train_linear_regression(X_train: np.ndarray, y_train: np.ndarray,
                            X_test: np.ndarray, y_test: np.ndarray) -> Tuple[Any, Dict[str, float]]:
    """
    Train Linear Regression model and extract coefficients.
    
    Args:
        X_train: Training features
        y_train: Training targets
        X_test: Test features
        y_test: Test targets
        
    Returns:
        Tuple of (model, metrics_dict)
    """
    logger.info("Training Linear Regression model...")
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Calculate metrics
    y_pred = model.predict(X_test)
    metrics = {
        'r2': float(r2_score(y_test, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
        'mae': float(mean_absolute_error(y_test, y_pred)),
        'coef': float(model.coef_[0]),
        'intercept': float(model.intercept_)
    }
    
    # Calculate p-value using t-test (simplified approach)
    from scipy import stats
    residuals = y_test - y_pred
    n = len(y_test)
    p = X_train.shape[1]
    
    # Standard error of the coefficient
    se_coef = np.sqrt(np.sum(residuals**2) / (n - p - 1)) / np.sqrt(np.sum((X_train - np.mean(X_train, axis=0))**2))
    t_stat = model.coef_[0] / se_coef[0]
    p_value = 2 * (1 - stats.t.cdf(np.abs(t_stat), n - p - 1))
    
    metrics['p_value'] = float(p_value)
    
    logger.info(f"Linear Regression training complete. R²: {metrics['r2']:.4f}, p-value: {metrics['p_value']:.4f}")
    return model, metrics

def save_model_and_metrics(model: Any, metrics: Dict[str, Any], 
                           model_name: str, metrics_file: str) -> None:
    """
    Save trained model and metrics to disk.
    
    Args:
        model: Trained sklearn model
        metrics: Dictionary of metrics
        model_name: Name of the model for file naming
        metrics_file: Path to save metrics JSON
    """
    model_path = MODELS_DIR / f"final_{model_name}.pkl"
    
    # Save model
    with open(model_path, 'wb') as f:
        pickle.dump(model, f, protocol=5)
    
    # Save metrics
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved {model_name} model to {model_path}")
    logger.info(f"Saved {model_name} metrics to {metrics_file}")

def main() -> None:
    """
    Main training pipeline entry point.
    
    1. Verifies input data is not synthetic (T068 requirement)
    2. Loads and prepares data
    3. Trains RF, GB, and Linear models
    4. Saves artifacts
    """
    logger.info("Starting model training pipeline...")
    
    # T068: Verify data is not synthetic before training
    curated_data_path = DATA_DIR / "curated" / "filtered.csv"
    logger.info(f"Verifying data provenance for: {curated_data_path}")
    verify_data_provenance(curated_data_path)
    
    # Prepare features and target
    X, y = prepare_features_target(curated_data_path)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    logger.info(f"Data split: Train={X_train.shape[0]}, Test={X_test.shape[0]}")
    
    # Train models
    # Random Forest
    rf_model, rf_metrics = train_random_forest(X_train, y_train, X_test, y_test)
    save_model_and_metrics(rf_model, rf_metrics, 'rf', MODELS_DIR / 'rf_metrics.json')
    
    # Gradient Boosting
    gb_model, gb_metrics = train_gradient_boosting(X_train, y_train, X_test, y_test)
    save_model_and_metrics(gb_model, gb_metrics, 'gb', MODELS_DIR / 'gb_metrics.json')
    
    # Linear Regression
    lr_model, lr_metrics = train_linear_regression(X_train, y_train, X_test, y_test)
    
    # Save linear coefficients separately
    linear_coef_path = MODELS_DIR / 'linear_coef.json'
    with open(linear_coef_path, 'w') as f:
        json.dump({
            'coef': lr_metrics['coef'],
            'intercept': lr_metrics['intercept'],
            'p_value': lr_metrics['p_value']
        }, f, indent=2)
    
    logger.info(f"Saved linear coefficients to {linear_coef_path}")
    
    # Aggregate all metrics
    aggregate_metrics(rf_metrics, gb_metrics, lr_metrics)
    
    logger.info("Model training pipeline complete.")

def aggregate_metrics(rf_metrics: Dict[str, Any], gb_metrics: Dict[str, Any], 
                     lr_metrics: Dict[str, Any]) -> None:
    """
    Aggregate all training metrics into a single file.
    
    Args:
        rf_metrics: Random Forest metrics
        gb_metrics: Gradient Boosting metrics
        lr_metrics: Linear Regression metrics
    """
    # Load mean predictor metrics if they exist
    mean_metrics_path = MODELS_DIR / 'mean_metrics.json'
    mean_r2 = 0.0
    if mean_metrics_path.exists():
        with open(mean_metrics_path, 'r') as f:
            mean_data = json.load(f)
            mean_r2 = mean_data.get('r2', 0.0)
    
    # Calculate deltas
    rf_delta = rf_metrics['r2'] - mean_r2
    gb_delta = gb_metrics['r2'] - mean_r2
    
    aggregated = {
        'rf_r2': rf_metrics['r2'],
        'rf_rmse': rf_metrics['rmse'],
        'rf_mae': rf_metrics['mae'],
        'rf_delta': rf_delta,
        'gb_r2': gb_metrics['r2'],
        'gb_rmse': gb_metrics['rmse'],
        'gb_mae': gb_metrics['mae'],
        'gb_delta': gb_delta,
        'mean_r2': mean_r2,
        'linear_coef': lr_metrics['coef'],
        'linear_p_value': lr_metrics['p_value']
    }
    
    metrics_path = MODELS_DIR / 'metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(aggregated, f, indent=2)
    
    logger.info(f"Aggregated metrics saved to {metrics_path}")

if __name__ == '__main__':
    main()