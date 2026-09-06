import json
import logging
import pickle
import signal
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, train_test_split

from config import MODELS_DIR, PROJECT_ROOT
from utils.logging import get_logger

logger = get_logger(__name__)

# Timeout duration in seconds (30 minutes)
GRIDSEARCH_TIMEOUT_SECONDS = 30 * 60


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Training Timeout: GridSearch exceeded 30min limit")


class TimeoutContext:
    """Context manager for timeout handling using signal."""
    def __init__(self, seconds):
        self.seconds = seconds

    def __enter__(self):
        # Only works on Unix systems with signal support
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel the alarm
        return False


def prepare_features_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, list]:
    """
    Prepare features (X) and target (y) from the curated dataframe.
    
    Args:
        df: Curated dataframe with descriptors and target column.
        
    Returns:
        X: Feature matrix
        y: Target vector
        feature_names: List of feature names
    """
    # Define features based on typical alloy diffusion descriptors
    # Assuming 'size_mismatch' is the primary feature as per T020
    feature_cols = [col for col in df.columns if col not in ['activation_energy', 'host_id', 'solute_id', 'concentration']]
    
    # Ensure we have at least one feature
    if 'size_mismatch' not in feature_cols:
        logger.warning("size_mismatch not found in columns. Using available numeric columns.")
        feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                        if col not in ['activation_energy']]
    
    feature_names = feature_cols
    X = df[feature_names].values
    y = df['activation_energy'].values
    
    return X, y, feature_names


def train_random_forest(X: np.ndarray, y: np.ndarray, feature_names: list) -> Tuple[Any, Dict]:
    """
    Train Random Forest with GridSearchCV and timeout protection.
    
    Args:
        X: Feature matrix
        y: Target vector
        feature_names: List of feature names
        
    Returns:
        best_model: Best trained model
        metrics: Dictionary of metrics
    """
    logger.info("Starting Random Forest training with GridSearch...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    param_grid = {
        'max_depth': [3, 5, 7, 10],
        'n_estimators': [50, 100, 150, 200]
    }
    
    rf = RandomForestRegressor(random_state=42, n_jobs=-1)
    
    grid_search = GridSearchCV(
        rf, 
        param_grid, 
        cv=5, 
        scoring='r2', 
        n_jobs=-1,
        verbose=1
    )
    
    try:
        with TimeoutContext(GRIDSEARCH_TIMEOUT_SECONDS):
            grid_search.fit(X_train, y_train)
    except TimeoutError as e:
        logger.error(str(e))
        raise SystemExit("Training Timeout: GridSearch exceeded 30min limit")
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Evaluate on test set
    y_pred = best_model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    
    metrics = {
        'r2': float(r2),
        'rmse': float(rmse),
        'mae': float(mae),
        'best_params': best_params,
        'cv_best_score': float(grid_search.best_score_)
    }
    
    logger.info(f"Random Forest R²: {r2:.4f}, RMSE: {rmse:.4f}")
    return best_model, metrics


def train_gradient_boosting(X: np.ndarray, y: np.ndarray, feature_names: list) -> Tuple[Any, Dict]:
    """
    Train Gradient Boosting with GridSearchCV and timeout protection.
    
    Args:
        X: Feature matrix
        y: Target vector
        feature_names: List of feature names
        
    Returns:
        best_model: Best trained model
        metrics: Dictionary of metrics
    """
    logger.info("Starting Gradient Boosting training with GridSearch...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    param_grid = {
        'max_depth': [3, 5, 7, 10],
        'n_estimators': [50, 100, 150, 200],
        'learning_rate': [0.05, 0.1, 0.2]
    }
    
    gb = GradientBoostingRegressor(random_state=42)
    
    grid_search = GridSearchCV(
        gb, 
        param_grid, 
        cv=5, 
        scoring='r2', 
        n_jobs=-1,
        verbose=1
    )
    
    try:
        with TimeoutContext(GRIDSEARCH_TIMEOUT_SECONDS):
            grid_search.fit(X_train, y_train)
    except TimeoutError as e:
        logger.error(str(e))
        raise SystemExit("Training Timeout: GridSearch exceeded 30min limit")
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Evaluate on test set
    y_pred = best_model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    
    metrics = {
        'r2': float(r2),
        'rmse': float(rmse),
        'mae': float(mae),
        'best_params': best_params,
        'cv_best_score': float(grid_search.best_score_)
    }
    
    logger.info(f"Gradient Boosting R²: {r2:.4f}, RMSE: {rmse:.4f}")
    return best_model, metrics


def train_linear_regression(X: np.ndarray, y: np.ndarray) -> Tuple[Any, Dict]:
    """
    Train Linear Regression and extract coefficient statistics.
    
    Args:
        X: Feature matrix
        y: Target vector
        
    Returns:
        model: Trained Linear Regression model
        metrics: Dictionary containing coefficient and p-value
    """
    logger.info("Training Linear Regression...")
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate R² on full data for reference
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    
    # For p-values, we use a simple approach since sklearn doesn't provide them directly
    # We'll use the first feature (size_mismatch) if available
    coef = model.coef_[0] if len(model.coef_) > 0 else 0.0
    intercept = model.intercept_
    
    # Simple p-value estimation using t-statistic approximation
    # This is a simplified version; for rigorous stats, use statsmodels
    n = len(y)
    p = X.shape[1]
    if n > p + 1:
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        mse = ss_res / (n - p - 1)
        
        # Standard error of coefficient (simplified)
        if len(X.shape) > 1 and X.shape[1] > 0:
            var_x = np.var(X[:, 0])
            if var_x > 0:
                se_coef = np.sqrt(mse / (n * var_x))
                t_stat = coef / se_coef if se_coef != 0 else 0
                # Approximate p-value using normal distribution for large n
                from scipy import stats
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - p - 1))
            else:
                p_value = 1.0
        else:
            p_value = 1.0
    else:
        p_value = 1.0
    
    metrics = {
        'r2': float(r2),
        'coefficient': float(coef),
        'intercept': float(intercept),
        'p_value': float(p_value)
    }
    
    logger.info(f"Linear Regression R²: {r2:.4f}, Coef: {coef:.4f}, p-value: {p_value:.4f}")
    return model, metrics


def save_model_and_metrics(model: Any, metrics: Dict, model_name: str, output_dir: Path):
    """
    Save trained model and metrics to disk.
    
    Args:
        model: Trained model object
        metrics: Dictionary of metrics
        model_name: Name of the model (e.g., 'rf', 'gb', 'linear')
        output_dir: Directory to save artifacts
    """
    model_path = output_dir / f'final_{model_name}.pkl'
    metrics_path = output_dir / f'{model_name}_metrics.json'
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f, protocol=5)
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved {model_name} model to {model_path}")
    logger.info(f"Saved {model_name} metrics to {metrics_path}")


def main():
    """Main entry point for training pipeline."""
    logger.info("Starting model training pipeline...")
    
    # Ensure directories exist
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load curated data
    curated_path = PROJECT_ROOT / 'data' / 'curated' / 'filtered.csv'
    if not curated_path.exists():
        logger.error(f"Curated data not found at {curated_path}")
        raise FileNotFoundError(f"Curated data not found at {curated_path}")
    
    df = pd.read_csv(curated_path)
    logger.info(f"Loaded {len(df)} rows from curated data")
    
    if len(df) < 10:
        logger.error("Insufficient data for training (N < 10)")
        raise ValueError("Insufficient data for training")
    
    # Prepare features and target
    X, y, feature_names = prepare_features_target(df)
    logger.info(f"Features: {feature_names}")
    
    # Train models
    rf_model, rf_metrics = train_random_forest(X, y, feature_names)
    save_model_and_metrics(rf_model, rf_metrics, 'rf', MODELS_DIR)
    
    gb_model, gb_metrics = train_gradient_boosting(X, y, feature_names)
    save_model_and_metrics(gb_model, gb_metrics, 'gb', MODELS_DIR)
    
    lr_model, lr_metrics = train_linear_regression(X, y)
    save_model_and_metrics(lr_model, lr_metrics, 'linear', MODELS_DIR)
    
    # Save linear coefficients separately for T023
    linear_coef_path = MODELS_DIR / 'linear_coef.json'
    with open(linear_coef_path, 'w') as f:
        json.dump({
            'coefficient': lr_metrics['coefficient'],
            'p_value': lr_metrics['p_value']
        }, f, indent=2)
    
    logger.info("Training pipeline completed successfully")
    return rf_model, gb_model, lr_model


if __name__ == '__main__':
    main()