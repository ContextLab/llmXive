"""
Random Forest training and evaluation module.
Implements nested cross-validation, hyperparameter tuning, and final model training.
"""
import os
import sys
import pickle
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib
from utils.config import get_runtime_config, check_obabel_timeout, get_joblib_parallel_backend

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

def load_fingerprints_and_targets(
    fingerprint_path: str,
    train_set_path: str,
    target_property: str = 'LogP'
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load fingerprints and corresponding target values from the training set.

    Args:
        fingerprint_path: Path to the parquet file containing fingerprints.
        train_set_path: Path to the CSV file containing the training set with targets.
        target_property: The property to predict (e.g., 'LogP', 'Solubility', 'Boiling Point').

    Returns:
        X: Fingerprints as a 2D numpy array.
        y: Target values as a 1D numpy array.
        smiles_list: List of SMILES strings corresponding to the rows.
    """
    logger.info(f"Loading fingerprints from {fingerprint_path}")
    logger.info(f"Loading training set from {train_set_path}")

    # Load fingerprints
    fp_df = pd.read_parquet(fingerprint_path)
    # Flatten fingerprint columns if they are stored as lists/arrays
    # Assuming columns are named 'maccs_bits', 'ecfp4_bits', 'fp2_bits' containing lists
    # We need to concatenate them into a single feature vector per molecule
    feature_cols = []
    for col in ['maccs_bits', 'ecfp4_bits', 'fp2_bits']:
        if col in fp_df.columns:
            # Expand list columns into separate feature columns
            expanded = pd.DataFrame(fp_df[col].tolist(), index=fp_df.index, prefix=f"{col}_")
            fp_df = pd.concat([fp_df.drop(columns=[col]), expanded], axis=1)
            feature_cols.extend(expanded.columns)

    X = fp_df[feature_cols].values.astype(np.float32)
    smiles_list = fp_df['smiles'].tolist()

    # Load training set to get targets
    train_df = pd.read_csv(train_set_path)
    # Merge on SMILES to align targets with fingerprints
    merged = train_df.merge(fp_df[['smiles']], on='smiles', how='inner')
    
    if target_property not in merged.columns:
        raise ValueError(f"Target property '{target_property}' not found in training set columns: {merged.columns.tolist()}")
    
    y = merged[target_property].values.astype(np.float32)
    smiles_list = merged['smiles'].tolist()

    logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features for {target_property}")
    return X, y, smiles_list

def reduce_dataset_size(
    X: np.ndarray, 
    y: np.ndarray, 
    max_samples: int = 2000, 
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reduce dataset size if it exceeds memory/time constraints.
    Uses stratified sampling if possible, otherwise random sampling.

    Args:
        X: Feature matrix.
        y: Target vector.
        max_samples: Maximum number of samples to keep.
        seed: Random seed for reproducibility.

    Returns:
        Reduced X and y.
    """
    if X.shape[0] <= max_samples:
        return X, y

    logger.warning(f"Dataset size ({X.shape[0]}) exceeds limit ({max_samples}). Reducing...")
    
    # For regression, we can't use StratifiedKFold directly on continuous targets.
    # We'll bin the targets to create pseudo-classes for stratified sampling.
    np.random.seed(seed)
    n_bins = min(10, max_samples // 100)
    if n_bins < 2:
        n_bins = 2
    
    # Create bins based on target distribution
    bin_edges = np.percentile(y, np.linspace(0, 100, n_bins + 1))
    y_binned = np.digitize(y, bin_edges)
    
    # Stratified split
    X_train, _, y_train, _ = train_test_split(
        X, y_binned, 
        train_size=max_samples, 
        stratify=y_binned, 
        random_state=seed
    )
    
    logger.info(f"Reduced dataset to {X_train.shape[0]} samples")
    return X_train, y_train

def tune_hyperparameters(
    X: np.ndarray, 
    y: np.ndarray, 
    param_grid: Dict[str, List],
    cv_folds: int = 5,
    seed: int = 42
) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """
    Perform grid search with cross-validation to tune hyperparameters.

    Args:
        X: Feature matrix.
        y: Target vector.
        param_grid: Dictionary of hyperparameters to search.
        cv_folds: Number of CV folds.
        seed: Random seed.

    Returns:
        best_model: The best model found.
        best_params: The best parameters found.
    """
    logger.info("Starting hyperparameter tuning with GridSearchCV...")
    
    rf_base = RandomForestRegressor(random_state=seed, n_jobs=-1)
    
    # Use StratifiedKFold logic if we bin targets, but for regression standard CV is fine
    # However, to ensure diversity, we can use KFold with shuffling
    from sklearn.model_selection import KFold
    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=seed)

    grid_search = GridSearchCV(
        estimator=rf_base,
        param_grid=param_grid,
        scoring='neg_mean_absolute_error',
        cv=cv,
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X, y)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best CV MAE: {-grid_search.best_score_:.4f}")
    
    return best_model, best_params

def run_nested_cross_validation(
    X: np.ndarray, 
    y: np.ndarray, 
    param_grid: Dict[str, List],
    outer_folds: int = 5,
    inner_folds: int = 5,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Perform nested cross-validation to estimate generalization error without bias.

    Args:
        X: Feature matrix.
        y: Target vector.
        param_grid: Hyperparameter grid.
        outer_folds: Number of outer CV folds.
        inner_folds: Number of inner CV folds.
        seed: Random seed.

    Returns:
        Dictionary containing outer CV scores and best parameters found in each fold.
    """
    logger.info("Starting nested cross-validation...")
    
    from sklearn.model_selection import KFold
    outer_cv = KFold(n_splits=outer_folds, shuffle=True, random_state=seed)
    inner_cv = KFold(n_splits=inner_folds, shuffle=True, random_state=seed)
    
    outer_scores = []
    fold_best_params = []
    
    for fold_idx, (train_idx, val_idx) in enumerate(outer_cv.split(X)):
        logger.info(f"Processing outer fold {fold_idx + 1}/{outer_folds}")
        
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        # Inner loop: Hyperparameter tuning
        rf_base = RandomForestRegressor(random_state=seed, n_jobs=-1)
        grid_search = GridSearchCV(
            estimator=rf_base,
            param_grid=param_grid,
            scoring='neg_mean_absolute_error',
            cv=inner_cv,
            n_jobs=-1,
            verbose=0
        )
        grid_search.fit(X_train, y_train)
        
        # Evaluate on outer validation set
        best_model = grid_search.best_estimator_
        y_pred = best_model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)
        outer_scores.append(mae)
        fold_best_params.append(grid_search.best_params_)
        
        logger.info(f"Outer fold {fold_idx + 1} MAE: {mae:.4f}")
    
    avg_mae = np.mean(outer_scores)
    logger.info(f"Nested CV Average MAE: {avg_mae:.4f} +/- {np.std(outer_scores):.4f}")
    
    return {
        'mean_mae': avg_mae,
        'std_mae': np.std(outer_scores),
        'fold_scores': outer_scores,
        'fold_best_params': fold_best_params
    }

def train_final_model(
    X: np.ndarray, 
    y: np.ndarray, 
    param_grid: Dict[str, List],
    seed: int = 42
) -> RandomForestRegressor:
    """
    Train the final model on the full training set using the best parameters found.

    Args:
        X: Full training feature matrix.
        y: Full training target vector.
        param_grid: Hyperparameter grid (used to find best params via CV on full set).
        seed: Random seed.

    Returns:
        Trained RandomForestRegressor model.
    """
    logger.info("Training final model on full dataset...")
    
    # We perform a final grid search on the full data to get the best params
    # Note: In strict nested CV, we use params from the inner loop of the outer CV,
    # but for the final model, we re-tune on the full data to maximize performance.
    best_model, best_params = tune_hyperparameters(X, y, param_grid, cv_folds=5, seed=seed)
    
    # Retrain with best params on full data (GridSearchCV already did this for the best param set)
    # But we ensure it's trained on ALL data
    final_model = RandomForestRegressor(**best_params, random_state=seed, n_jobs=-1)
    final_model.fit(X, y)
    
    logger.info("Final model training complete.")
    return final_model

def save_model(model: RandomForestRegressor, output_path: str) -> None:
    """
    Save the trained model to disk.

    Args:
        model: The trained model.
        output_path: Path to save the model.
    """
    logger.info(f"Saving model to {output_path}")
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info("Model saved successfully.")

def save_results(
    y_true: np.ndarray, 
    y_pred: np.ndarray, 
    smiles_list: List[str],
    output_path: str
) -> None:
    """
    Save predictions and residuals to a CSV file.

    Args:
        y_true: True values.
        y_pred: Predicted values.
        smiles_list: List of SMILES strings.
        output_path: Path to save the results.
    """
    df = pd.DataFrame({
        'smiles': smiles_list,
        'experimental_value': y_true,
        'predicted_value': y_pred,
        'residual': y_true - y_pred
    })
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def check_runtime_elapsed(start_time: float, max_seconds: float = 21600) -> bool:
    """
    Check if the maximum runtime has been exceeded.

    Args:
        start_time: Start time in seconds.
        max_seconds: Maximum allowed seconds (default 6 hours).

    Returns:
        True if time exceeded, False otherwise.
    """
    elapsed = time.time() - start_time
    if elapsed > max_seconds:
        logger.error(f"Runtime limit exceeded: {elapsed:.2f}s > {max_seconds}s")
        return True
    return False

def main():
    """
    Main entry point for training the Random Forest model.
    """
    start_time = time.time()
    
    # Configuration
    project_root = Path(__file__).resolve().parent.parent.parent
    fingerprint_path = project_root / 'data' / 'processed' / 'train_fingerprints.parquet'
    train_set_path = project_root / 'data' / 'derived' / 'train_set.csv'
    model_output_path = project_root / 'data' / 'derived' / 'final_model.pkl'
    
    # Hyperparameter grid
    param_grid = {
        'max_depth': [5, 10, 15],
        'n_estimators': [100, 200],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }
    
    # Target properties to train on (loop or select one)
    # For this task, we assume we are training on 'LogP' as the primary example
    # In a full pipeline, this might loop over properties
    target_property = 'LogP'
    
    logger.info(f"Starting RF training for {target_property}")
    
    # Check constraints
    if check_runtime_elapsed(start_time):
        sys.exit(1)
    
    # Load data
    try:
        X, y, smiles_list = load_fingerprints_and_targets(
            str(fingerprint_path), 
            str(train_set_path), 
            target_property
        )
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)
    
    # Reduce dataset if necessary (adaptive to resources)
    X, y = reduce_dataset_size(X, y, max_samples=3000, seed=42)
    
    if check_runtime_elapsed(start_time):
        sys.exit(1)
    
    # Run Nested Cross-Validation for unbiased error estimation
    # Note: This step estimates performance but does not produce the final model artifact
    nested_cv_results = run_nested_cross_validation(
        X, y, param_grid, outer_folds=5, inner_folds=5, seed=42
    )
    
    logger.info(f"Nested CV Results: MAE={nested_cv_results['mean_mae']:.4f}")
    
    if check_runtime_elapsed(start_time):
        sys.exit(1)
    
    # Train final model on the full training set
    final_model = train_final_model(X, y, param_grid, seed=42)
    
    if check_runtime_elapsed(start_time):
        sys.exit(1)
    
    # Save the final model
    ensure_dirs = model_output_path.parent
    ensure_dirs.mkdir(parents=True, exist_ok=True)
    save_model(final_model, str(model_output_path))
    
    logger.info("Task T020 completed successfully.")
    logger.info(f"Final model saved to: {model_output_path}")

if __name__ == "__main__":
    main()