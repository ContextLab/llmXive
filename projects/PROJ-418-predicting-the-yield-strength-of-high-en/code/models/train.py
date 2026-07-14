import os
import sys
import json
import time
import traceback
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from utils.logging import get_logger, get_seed

logger = get_logger(__name__)

# Constants for runtime tracking
MAX_RUNTIME_HOURS = 3
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600

def load_processed_data(filepath: str) -> pd.DataFrame:
    """Load processed data from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    return pd.read_csv(filepath)

def prepare_features_target(df: pd.DataFrame, target_col: str = 'yield_strength_mpa') -> Tuple[np.ndarray, np.ndarray]:
    """Separate features and target."""
    feature_cols = [col for col in df.columns if col not in [target_col, 'composition']]
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y

def create_stratified_split(X: np.ndarray, y: np.ndarray, test_size: float = 0.2, random_state: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create stratified train/test split."""
    if random_state is None:
        random_state = get_seed()
    
    # For regression, we bin the target for stratification
    y_binned = pd.qcut(y, q=10, labels=False, duplicates='drop')
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y_binned
    )
    return X_train, X_test, y_train, y_test

def save_split_info(split_info: Dict[str, Any], output_path: str):
    """Save split information to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(split_info, f, indent=2)

def train_linear_regression(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Tuple[LinearRegression, Dict[str, float]]:
    """Train Linear Regression baseline."""
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    metrics = {
        'r2': float(r2_score(y_test, y_pred)),
        'mae': float(mean_absolute_error(y_test, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }
    return model, metrics

def train_random_forest(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, max_runtime: float = MAX_RUNTIME_SECONDS) -> Tuple[RandomForestRegressor, Dict[str, float]]:
    """Train Random Forest with 5-fold CV and grid search."""
    start_time = time.time()
    
    param_grid = {
        'n_estimators': [10, 25, 50],
        'max_depth': [None, 5, 10]
    }
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=get_seed())
    y_binned = pd.qcut(y_train, q=10, labels=False, duplicates='drop')
    
    rf = RandomForestRegressor(random_state=get_seed())
    
    # Check runtime before each grid search step if possible, or run and check after
    grid_search = GridSearchCV(
        rf, param_grid, cv=cv, scoring='r2', n_jobs=-1, refit=True
    )
    
    grid_search.fit(X_train, y_train)
    
    elapsed = time.time() - start_time
    if elapsed > max_runtime:
        logger.warning(f"Random Forest training exceeded runtime limit: {elapsed:.2f}s > {max_runtime}s")
    
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    
    metrics = {
        'r2': float(r2_score(y_test, y_pred)),
        'mae': float(mean_absolute_error(y_test, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }
    
    logger.info(f"Random Forest best params: {grid_search.best_params_}")
    return best_model, metrics

def train_gradient_boosting(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, max_runtime: float = MAX_RUNTIME_SECONDS) -> Tuple[GradientBoostingRegressor, Dict[str, float]]:
    """Train Gradient Boosting with 5-fold CV and grid search."""
    start_time = time.time()
    
    param_grid = {
        'n_estimators': [10, 25, 50],
        'max_depth': [3, 5, 10],
        'learning_rate': [0.05, 0.1]
    }
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=get_seed())
    y_binned = pd.qcut(y_train, q=10, labels=False, duplicates='drop')
    
    gb = GradientBoostingRegressor(random_state=get_seed())
    
    grid_search = GridSearchCV(
        gb, param_grid, cv=cv, scoring='r2', n_jobs=-1, refit=True
    )
    
    grid_search.fit(X_train, y_train)
    
    elapsed = time.time() - start_time
    if elapsed > max_runtime:
        logger.warning(f"Gradient Boosting training exceeded runtime limit: {elapsed:.2f}s > {max_runtime}s")
    
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    
    metrics = {
        'r2': float(r2_score(y_test, y_pred)),
        'mae': float(mean_absolute_error(y_test, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }
    
    logger.info(f"Gradient Boosting best params: {grid_search.best_params_}")
    return best_model, metrics

def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """Evaluate a model on test set."""
    y_pred = model.predict(X_test)
    return {
        'r2': float(r2_score(y_test, y_pred)),
        'mae': float(mean_absolute_error(y_test, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }

def run_training_pipeline(
    data_path: str,
    output_dir: str,
    max_runtime_hours: int = MAX_RUNTIME_HOURS
) -> Dict[str, Any]:
    """
    Run the full training pipeline with runtime enforcement.
    
    Enforces a maximum runtime limit (default 3 hours). If the total
    training time exceeds this limit, a warning is logged and the
    pipeline attempts to save what has been completed so far.
    """
    start_total_time = time.time()
    max_total_seconds = max_runtime_hours * 3600
    
    logger.info(f"Starting training pipeline. Max runtime: {max_runtime_hours} hours")
    
    # Load data
    try:
        df = load_processed_data(data_path)
        logger.info(f"Loaded {len(df)} samples from {data_path}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {'status': 'error', 'message': str(e)}
    
    # Prepare features
    X, y = prepare_features_target(df)
    logger.info(f"Features shape: {X.shape}, Target shape: {y.shape}")
    
    # Split data
    X_train, X_test, y_train, y_test = create_stratified_split(X, y)
    logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Save split info
    split_info = {
        'train_size': len(X_train),
        'test_size': len(X_test),
        'feature_names': list(df.columns[df.columns != 'yield_strength_mpa' if 'yield_strength_mpa' in df.columns else df.columns[0]])
    }
    os.makedirs(output_dir, exist_ok=True)
    save_split_info(split_info, os.path.join(output_dir, 'split_info.json'))
    
    results = {
        'linear_regression': None,
        'random_forest': None,
        'gradient_boosting': None,
        'status': 'running',
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Train Linear Regression
    try:
        logger.info("Training Linear Regression...")
        lr_model, lr_metrics = train_linear_regression(X_train, y_train, X_test, y_test)
        results['linear_regression'] = lr_metrics
        logger.info(f"Linear Regression metrics: {lr_metrics}")
    except Exception as e:
        logger.error(f"Linear Regression failed: {e}")
        results['linear_regression'] = {'error': str(e)}
    
    # Check runtime
    elapsed = time.time() - start_total_time
    if elapsed > max_total_seconds:
        logger.warning(f"Runtime limit exceeded during Linear Regression. Total: {elapsed:.2f}s > {max_total_seconds}s")
        results['status'] = 'timeout'
        results['elapsed_seconds'] = elapsed
        return results
    
    # Train Random Forest
    try:
        logger.info("Training Random Forest...")
        rf_model, rf_metrics = train_random_forest(X_train, y_train, X_test, y_test, max_runtime=max_total_seconds - elapsed)
        results['random_forest'] = rf_metrics
        logger.info(f"Random Forest metrics: {rf_metrics}")
    except Exception as e:
        logger.error(f"Random Forest failed: {e}")
        results['random_forest'] = {'error': str(e)}
    
    # Check runtime
    elapsed = time.time() - start_total_time
    if elapsed > max_total_seconds:
        logger.warning(f"Runtime limit exceeded during Random Forest. Total: {elapsed:.2f}s > {max_total_seconds}s")
        results['status'] = 'timeout'
        results['elapsed_seconds'] = elapsed
        return results
    
    # Train Gradient Boosting
    try:
        logger.info("Training Gradient Boosting...")
        gb_model, gb_metrics = train_gradient_boosting(X_train, y_train, X_test, y_test, max_runtime=max_total_seconds - elapsed)
        results['gradient_boosting'] = gb_metrics
        logger.info(f"Gradient Boosting metrics: {gb_metrics}")
    except Exception as e:
        logger.error(f"Gradient Boosting failed: {e}")
        results['gradient_boosting'] = {'error': str(e)}
    
    # Finalize
    elapsed = time.time() - start_total_time
    results['status'] = 'completed' if elapsed <= max_total_seconds else 'timeout'
    results['elapsed_seconds'] = elapsed
    results['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
    
    if elapsed > max_total_seconds:
        logger.warning(f"TOTAL PIPELINE RUNTIME EXCEEDED LIMIT: {elapsed:.2f}s > {max_total_seconds}s")
    else:
        logger.info(f"Pipeline completed successfully in {elapsed:.2f}s")
    
    return results

def main():
    """Entry point for the training pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train HEA yield strength prediction models')
    parser.add_argument('--data', type=str, default='data/processed/hea_descriptors.csv',
                      help='Path to processed data CSV')
    parser.add_argument('--output', type=str, default='output',
                      help='Output directory for results')
    parser.add_argument('--max-runtime', type=int, default=3,
                      help='Maximum runtime in hours (default: 3)')
    
    args = parser.parse_args()
    
    results = run_training_pipeline(
        data_path=args.data,
        output_dir=args.output,
        max_runtime_hours=args.max_runtime
    )
    
    # Write results to metrics.json
    metrics_path = os.path.join(args.output, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {metrics_path}")
    
    if results.get('status') == 'timeout':
        logger.warning("Pipeline timed out. Some models may be incomplete.")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()