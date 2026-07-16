import os
import sys
import pickle
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib

from logging_utils import setup_logger
from seed_manager import set_global_seed

# Configure logger
logger = setup_logger(__name__)

# Constants for Runtime Monitoring
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours
MIN_DATASET_SIZE = 1000
FINGERPRINT_PRIORITY = ["ecfp4", "maccs", "fp2"]

def load_fingerprints_and_targets(
    fingerprint_path: Path,
    target_property: str,
    max_samples: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load fingerprints and targets from parquet file.
    Optionally limits samples for runtime monitoring.
    """
    logger.info(f"Loading fingerprints from {fingerprint_path}")
    df = pd.read_parquet(fingerprint_path)
    
    # Ensure we have the target column
    if target_property not in df.columns:
        raise ValueError(f"Target property '{target_property}' not found in dataset. Available: {df.columns.tolist()}")
    
    # Filter non-null targets
    df = df.dropna(subset=[target_property])
    
    # Apply max_samples limit if specified (for runtime monitoring)
    if max_samples is not None and len(df) > max_samples:
        logger.info(f"Limiting dataset to {max_samples} samples for runtime constraints")
        df = df.head(max_samples)
    
    X = df.drop(columns=[target_property]).values
    y = df[target_property].values
    
    logger.info(f"Loaded {len(X)} samples with shape {X.shape}")
    return X, y

def tune_hyperparameters(
    X: np.ndarray,
    y: np.ndarray,
    param_grid: Dict[str, Any],
    n_jobs: int = -1
) -> GridSearchCV:
    """
    Perform grid search for hyperparameter tuning.
    """
    logger.info("Starting hyperparameter tuning...")
    rf = RandomForestRegressor(random_state=42, n_jobs=1)
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=3,
        scoring='neg_mean_absolute_error',
        n_jobs=n_jobs,
        verbose=1
    )
    grid_search.fit(X, y)
    logger.info(f"Best parameters: {grid_search.best_params_}")
    return grid_search

def run_nested_cross_validation(
    X: np.ndarray,
    y: np.ndarray,
    param_grid: Dict[str, Any],
    n_jobs: int = -1
) -> Dict[str, Any]:
    """
    Run nested cross-validation to get unbiased performance estimates.
    Outer loop: 5-fold CV for testing
    Inner loop: GridSearchCV for tuning
    """
    logger.info("Starting nested cross-validation...")
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # We need to convert y to integer bins for StratifiedKFold if it's continuous
    # Discretize y into 10 bins for stratification
    y_bins = pd.qcut(y, q=10, labels=False, duplicates='drop')
    
    outer_scores = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y_bins)):
        logger.info(f"Processing outer fold {fold_idx + 1}/5")
        
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Inner loop: Hyperparameter tuning
        inner_search = tune_hyperparameters(X_train, y_train, param_grid, n_jobs=n_jobs)
        best_model = inner_search.best_estimator_
        
        # Evaluate on test set
        y_pred = best_model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        outer_scores.append({'mae': mae, 'rmse': rmse})
        logger.info(f"Fold {fold_idx + 1} - MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    
    avg_mae = np.mean([s['mae'] for s in outer_scores])
    avg_rmse = np.mean([s['rmse'] for s in outer_scores])
    
    return {
        'mae': avg_mae,
        'rmse': avg_rmse,
        'fold_scores': outer_scores
    }

def train_final_model(
    X: np.ndarray,
    y: np.ndarray,
    param_grid: Dict[str, Any],
    n_jobs: int = -1
) -> RandomForestRegressor:
    """
    Train the final model on the full dataset with best parameters.
    """
    logger.info("Training final model on full dataset...")
    grid_search = tune_hyperparameters(X, y, param_grid, n_jobs=n_jobs)
    return grid_search.best_estimator_

def save_model(model: RandomForestRegressor, output_path: Path):
    """
    Save the trained model to disk.
    """
    logger.info(f"Saving model to {output_path}")
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info("Model saved successfully")

def save_results(
    results: Dict[str, Any],
    output_path: Path
):
    """
    Save evaluation results to CSV.
    """
    logger.info(f"Saving results to {output_path}")
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_path, index=False)
    logger.info("Results saved successfully")

def check_runtime_elapsed(start_time: float) -> bool:
    """
    Check if the elapsed time exceeds the maximum allowed runtime.
    Returns True if time limit is exceeded.
    """
    elapsed = time.time() - start_time
    if elapsed > MAX_RUNTIME_SECONDS:
        logger.warning(f"Runtime limit exceeded: {elapsed:.1f}s > {MAX_RUNTIME_SECONDS}s")
        return True
    return False

def reduce_dataset_size(
    X: np.ndarray,
    y: np.ndarray,
    reduction_factor: float = 0.5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reduce dataset size by sampling.
    """
    n_samples = len(X)
    new_size = max(MIN_DATASET_SIZE, int(n_samples * reduction_factor))
    logger.info(f"Reducing dataset from {n_samples} to {new_size} samples")
    
    indices = np.random.choice(n_samples, size=new_size, replace=False)
    return X[indices], y[indices]

def skip_fingerprint(fingerprint_type: str) -> bool:
    """
    Determine if a fingerprint type should be skipped based on priority.
    Returns True if it should be skipped (lower priority).
    """
    priority_index = FINGERPRINT_PRIORITY.index(fingerprint_type) if fingerprint_type in FINGERPRINT_PRIORITY else len(FINGERPRINT_PRIORITY)
    # Skip if it's the lowest priority (fp2) and we are under time pressure
    return priority_index == len(FINGERPRINT_PRIORITY) - 1

def main():
    """
    Main entry point for Random Forest training with runtime monitoring.
    """
    set_global_seed(42)
    
    # Configuration
    fingerprint_file = Path("data/derived/fingerprints.parquet")
    target_property = "logP"  # Can be configured
    model_output = Path("data/derived/final_model.pkl")
    results_output = Path("data/derived/nested_cv_results.csv")
    
    # Hyperparameter grid
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [10, 20, None],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }
    
    start_time = time.time()
    
    try:
        # Load data
        if not fingerprint_file.exists():
            raise FileNotFoundError(f"Fingerprint file not found: {fingerprint_file}")
        
        X, y = load_fingerprints_and_targets(fingerprint_file, target_property)
        
        # Initial runtime check
        if check_runtime_elapsed(start_time):
            logger.error("Time limit exceeded before starting training")
            sys.exit(1)
        
        # Check if dataset is too large and reduce if necessary
        if len(X) > 5000:
            logger.warning(f"Dataset size ({len(X)}) exceeds recommended limit (5000). Reducing...")
            X, y = reduce_dataset_size(X, y, 0.6)
        
        # Run nested cross-validation
        cv_results = run_nested_cross_validation(X, y, param_grid)
        
        # Check runtime after CV
        if check_runtime_elapsed(start_time):
            logger.error("Time limit exceeded during cross-validation")
            sys.exit(1)
        
        # Train final model
        final_model = train_final_model(X, y, param_grid)
        
        # Check runtime after training
        if check_runtime_elapsed(start_time):
            logger.error("Time limit exceeded during final model training")
            sys.exit(1)
        
        # Save artifacts
        save_model(final_model, model_output)
        save_results(cv_results['fold_scores'], results_output)
        
        logger.info(f"Training completed successfully. MAE: {cv_results['mae']:.4f}, RMSE: {cv_results['rmse']:.4f}")
        
    except Exception as e:
        logger.error(f"Error during training: {e}")
        raise
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Total runtime: {elapsed:.1f}s")

if __name__ == "__main__":
    main()