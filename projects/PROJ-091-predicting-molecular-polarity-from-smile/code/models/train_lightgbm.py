"""
LightGBM Training Module for Molecular Polarity Prediction.

This module handles data loading from split files, model training, cross-validation,
hyperparameter tuning, evaluation, and model persistence. It is optimized for
CPU-only execution with specific threading and verbosity controls.

Key Features:
- Loading data from parquet split files.
- Training LightGBM Regressor with configurable parameters.
- K-fold cross-validation for robust hyperparameter tuning.
- Automatic saving of optimal parameters to config.yaml.
- Evaluation against a null model baseline.

Constraints:
- No 3D conformer generation or TPSA calculations are performed here;
  this module assumes pre-computed 2D descriptors.
- Optimized for CPU execution (num_threads, verbose settings).
"""

import os
import sys
import logging
import pickle
import gc
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.dummy import DummyRegressor

# Local imports
# Note: Imports must match the API surface provided in the prompt context
# Assuming config utilities are available in utils.config
try:
    from utils.config import load_hyperparameters, TrainingConfig
except ImportError:
    # Fallback for standalone execution if utils is not in path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.config import load_hyperparameters, TrainingConfig

from utils.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# ============================================================================
# Data Loading
# ============================================================================

def load_data_from_splits(splits_dir: Union[str, Path]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads train, validation, and test data from the split parquet files.

    Expected files in splits_dir:
    - train.parquet
    - val.parquet
    - test.parquet

    Args:
        splits_dir: Path to the directory containing split files.

    Returns:
        Tuple of (X_train, y_train, X_val, y_val, X_test, y_test)
        (Actually returns 6 items, but signature shows 4 for brevity in docstring,
         implementation returns 6).
    """
    splits_dir = Path(splits_dir)
    train_path = splits_dir / "train.parquet"
    val_path = splits_dir / "val.parquet"
    test_path = splits_dir / "test.parquet"

    if not train_path.exists() or not val_path.exists() or not test_path.exists():
        raise FileNotFoundError(f"Split files not found in {splits_dir}. Expected: train.parquet, val.parquet, test.parquet")

    logger.info(f"Loading training data from {train_path}")
    df_train = pd.read_parquet(train_path)
    logger.info(f"Loading validation data from {val_path}")
    df_val = pd.read_parquet(val_path)
    logger.info(f"Loading test data from {test_path}")
    df_test = pd.read_parquet(test_path)

    # Separate features and target
    # Assuming 'target' column exists as per data model
    target_col = 'target'
    feature_cols = [c for c in df_train.columns if c != target_col and c != 'smiles']

    X_train = df_train[feature_cols]
    y_train = df_train[target_col]
    X_val = df_val[feature_cols]
    y_val = df_val[target_col]
    X_test = df_test[feature_cols]
    y_test = df_test[target_col]

    logger.info(f"Data loaded: Train {X_train.shape}, Val {X_val.shape}, Test {X_test.shape}")
    return X_train, y_train, X_val, y_val, X_test, y_test

# ============================================================================
# Model Training & Tuning
# ============================================================================

def train_base_model(X_train: pd.DataFrame, y_train: pd.Series, 
                     X_val: pd.DataFrame, y_val: pd.Series, 
                     params: Dict[str, Any]) -> lgb.Booster:
    """
    Trains a base LightGBM model.

    Args:
        X_train: Training features.
        y_train: Training targets.
        X_val: Validation features.
        y_val: Validation targets.
        params: Hyperparameters dictionary.

    Returns:
        Trained LightGBM Booster.
    """
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

    # CPU Optimization:
    # num_threads: Set to 1 to avoid overhead in single-process execution
    # verbose: -1 to suppress training logs during tuning loops
    params_cpu = params.copy()
    params_cpu['num_threads'] = 1
    params_cpu['verbose'] = -1

    logger.info("Training LightGBM model with CPU optimizations...")
    model = lgb.train(
        params_cpu,
        train_data,
        valid_sets=[val_data],
        valid_names=['val'],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
    )
    return model

def cross_validate_model(X: pd.DataFrame, y: pd.Series, 
                         params: Dict[str, Any], 
                         n_splits: int = 5) -> Tuple[float, float]:
    """
    Performs k-fold cross-validation to evaluate model performance.

    Args:
        X: Features.
        y: Targets.
        params: Hyperparameters.
        n_splits: Number of CV folds.

    Returns:
        Tuple of (mean_r2, std_r2).
    """
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    r2_scores = []

    # CPU Optimization: Ensure num_threads is 1 for CV to prevent thread contention
    params_cv = params.copy()
    params_cv['num_threads'] = 1
    params_cv['verbose'] = -1

    for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]

        train_set = lgb.Dataset(X_tr, label=y_tr)
        val_set = lgb.Dataset(X_val, label=y_val, reference=train_set)

        model = lgb.train(
            params_cv,
            train_set,
            valid_sets=[val_set],
            callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
        )

        preds = model.predict(X_val)
        r2 = r2_score(y_val, preds)
        r2_scores.append(r2)
        
        # Force garbage collection to manage memory during CV
        del model, train_set, val_set
        gc.collect()

    mean_r2 = np.mean(r2_scores)
    std_r2 = np.std(r2_scores)
    logger.info(f"CV R2: {mean_r2:.4f} (+/- {std_r2:.4f})")
    return mean_r2, std_r2

def tune_hyperparameters(X: pd.DataFrame, y: pd.Series, 
                         base_params: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
    """
    Performs grid search / simple tuning over hyperparameters.
    Optimizes for R2 score.

    Args:
        X: Features.
        y: Targets.
        base_params: Base hyperparameters.

    Returns:
        Tuple of (best_params, best_score).
    """
    logger.info("Starting hyperparameter tuning...")
    
    # Define search space
    param_grid = {
        'num_leaves': [31, 63, 127],
        'learning_rate': [0.01, 0.05, 0.1],
        'n_estimators': [100, 200, 500]
    }

    best_score = -np.inf
    best_params = base_params.copy()

    # CPU Optimization:
    # We set num_threads=1 and verbose=-1 in the base_params before tuning
    # to ensure the tuning loop is fast and silent.
    base_params['num_threads'] = 1
    base_params['verbose'] = -1

    for nl in param_grid['num_leaves']:
        for lr in param_grid['learning_rate']:
            for ne in param_grid['n_estimators']:
                current_params = base_params.copy()
                current_params['num_leaves'] = nl
                current_params['learning_rate'] = lr
                current_params['n_estimators'] = ne

                # We use a subset for tuning speed if dataset is huge, 
                # but for now we run CV on full data as per spec.
                # To keep it fast, we might reduce folds or use a smaller sample
                # if time is critical, but here we stick to standard CV.
                score, _ = cross_validate_model(X, y, current_params, n_splits=3)
                
                if score > best_score:
                    best_score = score
                    best_params = current_params
                    logger.info(f"New best: num_leaves={nl}, lr={lr}, n_est={ne}, R2={score:.4f}")

    logger.info(f"Tuning complete. Best R2: {best_score:.4f}")
    return best_params, best_score

def evaluate_model(model: lgb.Booster, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """
    Evaluates the model on the test set.

    Args:
        model: Trained LightGBM model.
        X_test: Test features.
        y_test: Test targets.

    Returns:
        Dictionary with R2 and RMSE.
    """
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    
    logger.info(f"Test R2: {r2:.4f}, RMSE: {rmse:.4f}")
    return {'r2': r2, 'rmse': rmse}

def compute_null_model_r2(X_train: pd.DataFrame, y_train: pd.Series, 
                          X_test: pd.DataFrame, y_test: pd.Series) -> float:
    """
    Computes R2 for a dummy model (predicting mean) to establish baseline.

    Returns:
        R2 score of the null model (should be ~0.0).
    """
    dummy = DummyRegressor(strategy='mean')
    dummy.fit(X_train, y_train)
    preds = dummy.predict(X_test)
    return r2_score(y_test, preds)

# ============================================================================
# Persistence & Configuration
# ============================================================================

def save_model(model: lgb.Booster, filepath: Union[str, Path]):
    """Saves the model to a pickle file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {filepath}")

def update_config_with_params(best_params: Dict[str, Any], config_path: Union[str, Path]):
    """
    Updates the config.yaml file with the best hyperparameters found.
    
    Args:
        best_params: Dictionary of best parameters.
        config_path: Path to the config.yaml file.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        logger.warning(f"Config file {config_path} not found. Creating new one.")
        # Create a basic structure if missing
        base_config = {'training': {}}
    else:
        import yaml
        with open(config_path, 'r') as f:
            base_config = yaml.safe_load(f) or {}
    
    if 'training' not in base_config:
        base_config['training'] = {}
    
    # Update specific keys
    base_config['training'].update({
        'num_leaves': best_params.get('num_leaves'),
        'learning_rate': best_params.get('learning_rate'),
        'n_estimators': best_params.get('n_estimators'),
        'num_threads': best_params.get('num_threads', 1), # Ensure it's saved
        'verbose': best_params.get('verbose', -1)
    })
    
    with open(config_path, 'w') as f:
        yaml.dump(base_config, f, default_flow_style=False)
    logger.info(f"Updated config with best params at {config_path}")

# ============================================================================
# Main Orchestrator
# ============================================================================

def train_lightgbm(
    splits_dir: Union[str, Path] = "data/processed",
    model_dir: Union[str, Path] = "data/processed",
    config_path: Union[str, Path] = "code/config.yaml",
    force_tune: bool = False
):
    """
    Main entry point for training the LightGBM model.
    
    1. Loads data.
    2. Tunes hyperparameters (if force_tune or no config).
    3. Trains final model.
    4. Evaluates and saves.
    
    Args:
        splits_dir: Directory containing train/val/test.parquet.
        model_dir: Directory to save model.pkl.
        config_path: Path to config.yaml.
        force_tune: If True, forces re-tuning.
    """
    splits_dir = Path(splits_dir)
    model_dir = Path(model_dir)
    config_path = Path(config_path)
    
    # Load data
    X_train, y_train, X_val, y_val, X_test, y_test = load_data_from_splits(splits_dir)
    
    # Load base parameters
    try:
        config = load_hyperparameters(config_path)
        base_params = config.training if hasattr(config, 'training') else {}
        if isinstance(base_params, dict):
            base_params = base_params
        else:
            base_params = {}
    except Exception as e:
        logger.warning(f"Could not load config: {e}. Using defaults.")
        base_params = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'n_estimators': 200
        }
    
    # Ensure CPU optimizations are set
    base_params['num_threads'] = 1
    base_params['verbose'] = -1
    
    # Tune if needed
    if force_tune or not config_path.exists():
        best_params, best_score = tune_hyperparameters(X_train, y_train, base_params)
        update_config_with_params(best_params, config_path)
        final_params = best_params
    else:
        logger.info("Using existing hyperparameters from config.")
        final_params = base_params
    
    # Train final model on train + val
    X_final = pd.concat([X_train, X_val], axis=0)
    y_final = pd.concat([y_train, y_val], axis=0)
    
    train_data = lgb.Dataset(X_final, label=y_final)
    model = lgb.train(
        final_params,
        train_data,
        num_boost_round=final_params.get('n_estimators', 200)
    )
    
    # Evaluate
    results = evaluate_model(model, X_test, y_test)
    null_r2 = compute_null_model_r2(X_train, y_train, X_test, y_test)
    
    if results['r2'] <= null_r2:
        logger.error(f"Model R2 ({results['r2']:.4f}) <= Null Model R2 ({null_r2:.4f}). Training failed.")
    else:
        logger.info(f"Model improved over null model by {results['r2'] - null_r2:.4f}")
    
    # Save
    model_path = model_dir / "model.pkl"
    save_model(model, model_path)
    
    return model, results

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Train LightGBM for Molecular Polarity")
    parser.add_argument('--splits-dir', type=str, default='data/processed', help='Directory with split files')
    parser.add_argument('--model-dir', type=str, default='data/processed', help='Directory to save model')
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config.yaml')
    parser.add_argument('--tune', action='store_true', help='Force hyperparameter tuning')
    
    args = parser.parse_args()
    
    train_lightgbm(
        splits_dir=args.splits_dir,
        model_dir=args.model_dir,
        config_path=args.config,
        force_tune=args.tune
    )

if __name__ == "__main__":
    main()