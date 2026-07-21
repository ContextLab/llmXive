"""
Random Forest model training and validation module.

This module implements nested cross-validation, hyperparameter tuning,
and model training for molecular property prediction using Open Babel fingerprints.
"""
import os
import sys
import pickle
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score, StratifiedKFold
from sklearn.metrics import mean_absolute_error, mean_squared_error
from joblib import Parallel, delayed
import joblib

# Configure logging
logger = logging.getLogger(__name__)

def load_fingerprints_and_targets(train_path: str, target_column: str = 'logP') -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load fingerprints and target values from the training set.

    Args:
        train_path: Path to the training set CSV file.
        target_column: Name of the target column.

    Returns:
        Tuple of (fingerprints array, target array, feature names).
    """
    df = pd.read_csv(train_path)
    # Assume first column is SMILES, last is target, rest are fingerprints
    smiles_col = df.columns[0]
    target_col = df.columns[-1]
    fingerprint_cols = df.columns[1:-1]

    fingerprints = df[fingerprint_cols].values
    targets = df[target_col].values
    feature_names = fingerprint_cols.tolist()

    return fingerprints, targets, feature_names

def tune_hyperparameters(X: np.ndarray, y: np.ndarray, n_splits: int = 3) -> Dict[str, Any]:
    """
    Tune Random Forest hyperparameters using cross-validation.

    Args:
        X: Feature matrix.
        y: Target vector.
        n_splits: Number of CV splits.

    Returns:
        Dictionary of best hyperparameters.
    """
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [10, 15],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }

    rf = RandomForestRegressor(random_state=42, n_jobs=-1)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    # For regression, we need to create dummy classes for stratification
    # Use quartiles of y for stratification
    y_quantiles = pd.qcut(y, q=n_splits, labels=False)

    grid_search = GridSearchCV(
        rf, param_grid, cv=cv, scoring='neg_mean_absolute_error', n_jobs=-1
    )
    grid_search.fit(X, y, y=y_quantiles)

    best_params = grid_search.best_params_
    logger.info(f"Best hyperparameters: {best_params}")
    return best_params

def run_nested_cross_validation(
    X: np.ndarray,
    y: np.ndarray,
    outer_n_splits: int = 5,
    inner_n_splits: int = 3
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Run nested cross-validation for unbiased error estimation.

    Args:
        X: Feature matrix.
        y: Target vector.
        outer_n_splits: Number of outer CV splits.
        inner_n_splits: Number of inner CV splits.

    Returns:
        Tuple of (out-of-fold predictions, true values, best params).
    """
    n_samples = len(y)
    oof_predictions = np.zeros(n_samples)
    best_params_list = []

    outer_cv = StratifiedKFold(n_splits=outer_n_splits, shuffle=True, random_state=42)
    y_quantiles = pd.qcut(y, q=outer_n_splits, labels=False)

    for fold_idx, (train_idx, val_idx) in enumerate(outer_cv.split(X, y_quantiles)):
        logger.info(f"Processing outer fold {fold_idx + 1}/{outer_n_splits}")

        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        # Tune hyperparameters on training fold
        best_params = tune_hyperparameters(X_train, y_train, n_splits=inner_n_splits)
        best_params_list.append(best_params)

        # Train model with best params
        model = RandomForestRegressor(**best_params, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)

        # Predict on validation fold
        oof_predictions[val_idx] = model.predict(X_val)

    # Average best params
    avg_params = {
        'n_estimators': int(np.mean([p['n_estimators'] for p in best_params_list])),
        'max_depth': int(np.mean([p['max_depth'] for p in best_params_list])),
        'min_samples_split': int(np.mean([p['min_samples_split'] for p in best_params_list])),
        'min_samples_leaf': int(np.mean([p['min_samples_leaf'] for p in best_params_list]))
    }

    return oof_predictions, y, avg_params

def train_final_model(X: np.ndarray, y: np.ndarray, params: Dict[str, Any]) -> RandomForestRegressor:
    """
    Train the final model on the full training set.

    Args:
        X: Full feature matrix.
        y: Full target vector.
        params: Hyperparameters to use.

    Returns:
        Trained Random Forest model.
    """
    logger.info("Training final model...")
    model = RandomForestRegressor(**params, random_state=42, n_jobs=-1)
    model.fit(X, y)
    return model

def save_model(model: RandomForestRegressor, output_path: str) -> None:
    """
    Save the trained model to disk.

    Args:
        model: Trained model.
        output_path: Path to save the model.
    """
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {output_path}")

def save_results(
    oof_predictions: np.ndarray,
    true_values: np.ndarray,
    metrics: Dict[str, float],
    output_path: str
) -> None:
    """
    Save cross-validation results to disk.

    Args:
        oof_predictions: Out-of-fold predictions.
        true_values: True target values.
        metrics: Dictionary of performance metrics.
        output_path: Path to save the results.
    """
    results_df = pd.DataFrame({
        'true': true_values,
        'predicted': oof_predictions
    })
    results_df.to_csv(output_path, index=False)

    with open(output_path.replace('.csv', '_metrics.json'), 'w') as f:
        import json
        json.dump(metrics, f, indent=2)

    logger.info(f"Results saved to {output_path}")

def check_runtime_elapsed(start_time: float, max_time: float = 21600) -> bool:
    """
    Check if the runtime has exceeded the maximum allowed time.

    Args:
        start_time: Start time of the process.
        max_time: Maximum allowed time in seconds (default 6 hours).

    Returns:
        True if time limit exceeded, False otherwise.
    """
    elapsed = time.time() - start_time
    if elapsed > max_time:
        logger.warning(f"Runtime limit exceeded: {elapsed:.1f}s > {max_time}s")
        return True
    return False

def reduce_dataset_size(X: np.ndarray, y: np.ndarray, max_samples: int = 5000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reduce dataset size if it exceeds the maximum allowed.

    Args:
        X: Feature matrix.
        y: Target vector.
        max_samples: Maximum number of samples.

    Returns:
        Reduced feature matrix and target vector.
    """
    if len(X) <= max_samples:
        return X, y

    logger.info(f"Reducing dataset from {len(X)} to {max_samples} samples")
    indices = np.random.choice(len(X), max_samples, replace=False)
    return X[indices], y[indices]

def skip_fingerprint(fingerprint_name: str, time_budget_remaining: float) -> bool:
    """
    Determine if a fingerprint should be skipped due to time constraints.

    Args:
        fingerprint_name: Name of the fingerprint.
        time_budget_remaining: Remaining time budget in seconds.

    Returns:
        True if fingerprint should be skipped, False otherwise.
    """
    # Prioritize ECFP4 > MACCS > FP2
    priority = {'ECFP4': 1, 'MACCS': 2, 'FP2': 3}
    current_priority = priority.get(fingerprint_name, 999)

    if time_budget_remaining < 3600:  # Less than 1 hour left
        return current_priority > 1

    return False

def main() -> None:
    """
    Main entry point for the Random Forest training pipeline.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Define paths
    project_root = Path(__file__).parent.parent.parent
    train_path = project_root / 'data' / 'derived' / 'train_set.csv'
    output_dir = project_root / 'data' / 'derived'

    if not train_path.exists():
        logger.error(f"Training set not found: {train_path}")
        sys.exit(1)

    start_time = time.time()

    # Load data
    logger.info("Loading training data...")
    X, y, feature_names = load_fingerprints_and_targets(str(train_path))

    # Check dataset size
    X, y = reduce_dataset_size(X, y, max_samples=5000)

    # Run nested cross-validation
    logger.info("Running nested cross-validation...")
    oof_predictions, true_values, best_params = run_nested_cross_validation(X, y, outer_n_splits=5, inner_n_splits=3)

    # Calculate metrics
    mae = mean_absolute_error(true_values, oof_predictions)
    rmse = np.sqrt(mean_squared_error(true_values, oof_predictions))
    metrics = {
        'MAE': mae,
        'RMSE': rmse,
        'n_samples': len(y),
        'best_params': best_params
    }

    # Train final model
    final_model = train_final_model(X, y, best_params)

    # Save results
    save_results(oof_predictions, true_values, metrics, str(output_dir / 'rf_oof_predictions.csv'))
    save_model(final_model, str(output_dir / 'final_model.pkl'))

    elapsed = time.time() - start_time
    logger.info(f"Training complete in {elapsed:.1f}s")
    logger.info(f"Nested CV MAE: {mae:.4f}, RMSE: {rmse:.4f}")

if __name__ == "__main__":
    main()
