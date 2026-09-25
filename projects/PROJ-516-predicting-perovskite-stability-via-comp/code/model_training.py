"""
Model Training Module for Perovskite Stability Prediction.

Implements Random Forest, Gradient Boosting, and Elastic Net models with
uncertainty-based sample weighting and configurable low-confidence down-weighting.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_PATH = "data/processed/descriptors.csv"
OUTPUT_PATH = "data/processed/model_runs.json"
CONFIG_PATH = "code/config.yaml"

def load_config() -> Dict[str, Any]:
    """Load configuration from code/config.yaml."""
    if not os.path.exists(CONFIG_PATH):
        logger.warning(f"Config file {CONFIG_PATH} not found. Using defaults.")
        return {
            "model": {
                "low_confidence_weight": 0.5,
                "max_grid_search_combinations": 10,
                "k_folds": 5
            }
        }
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_data() -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load the processed dataset and prepare features/target.

    Returns:
        Tuple of (df, X, y, y_strat) where:
        - df: Full dataframe
        - X: Feature matrix
        - y: Target vector (T_d)
        - y_strat: Stratification labels (perovskite_family)
    """
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data file {DATA_PATH} not found. Run T017 first.")

    df = pd.read_csv(DATA_PATH)

    # Required columns
    required_cols = ['T_d', 'perovskite_family']
    feature_cols = [
        'atomic_fraction_A', 'atomic_fraction_B', 'atomic_fraction_X',
        'weighted_ionic_radius', 'weighted_electronegativity',
        'weighted_formation_enthalpy', 'first_ionization_energy',
        'variance_ionic_radius', 'variance_electronegativity'
    ]

    missing_cols = [c for c in required_cols + feature_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {DATA_PATH}: {missing_cols}")

    # Filter out rows with missing target or features
    df = df.dropna(subset=['T_d'] + feature_cols)
    if len(df) == 0:
        raise ValueError("No valid data points remaining after filtering.")

    X = df[feature_cols].values
    y = df['T_d'].values
    y_strat = df['perovskite_family'].values

    return df, X, y, y_strat

def compute_sample_weights(df: pd.DataFrame, config: Dict[str, Any]) -> np.ndarray:
    """
    Compute sample weights based on uncertainty and confidence flags.

    Weights are calculated as:
    1. Base weight = 1 / (total_uncertainty^2)
    2. If confidence_flag == 'low', multiply by low_confidence_weight from config.

    Args:
        df: DataFrame containing 'total_uncertainty' and 'confidence_flag' columns.
        config: Configuration dictionary.

    Returns:
        Array of sample weights.
    """
    low_conf_weight = config.get('model', {}).get('low_confidence_weight', 0.5)

    if 'total_uncertainty' not in df.columns:
        raise ValueError("Column 'total_uncertainty' not found in data. Run T061 first.")

    # Avoid division by zero
    uncertainties = df['total_uncertainty'].replace(0, 1e-6).values
    base_weights = 1.0 / (uncertainties ** 2)

    # Apply low confidence penalty
    if 'confidence_flag' in df.columns:
        confidence_flags = df['confidence_flag'].values
        mask_low_conf = (confidence_flags == 'low')
        base_weights[mask_low_conf] *= low_conf_weight
        logger.info(f"Applied low_confidence_weight ({low_conf_weight}) to {mask_low_conf.sum()} low-confidence samples.")
    else:
        logger.warning("Column 'confidence_flag' not found. Skipping low-confidence adjustment.")

    return base_weights

def train_random_forest(X: np.ndarray, y: np.ndarray, sample_weights: np.ndarray,
                        stratification: np.ndarray, config: Dict[str, Any]) -> Dict[str, Any]:
    """Train Random Forest with cross-validation and grid search."""
    logger.info("Training Random Forest...")
    k_folds = config.get('model', {}).get('k_folds', 5)
    max_combos = config.get('model', {}).get('max_grid_search_combinations', 10)

    # Simple grid: limit to max_combos
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [None, 10, 20]
    }
    # Flatten and limit
    combos = []
    for n in param_grid['n_estimators']:
        for d in param_grid['max_depth']:
            combos.append({'n_estimators': n, 'max_depth': d})
    param_grid = combos[:max_combos]

    best_score = -np.inf
    best_params = None
    best_model = None
    metrics_log = []

    skf = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=42)

    for params in param_grid:
        fold_scores = []
        for train_idx, val_idx in skf.split(X, stratification):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            w_train = sample_weights[train_idx]

            model = RandomForestRegressor(**params, random_state=42, n_jobs=-1)
            model.fit(X_train, y_train, sample_weight=w_train)

            y_pred = model.predict(X_val)
            r2 = r2_score(y_val, y_pred)
            fold_scores.append(r2)

        mean_r2 = np.mean(fold_scores)
        metrics_log.append({
            'params': params,
            'mean_r2': float(mean_r2),
            'std_r2': float(np.std(fold_scores))
        })

        if mean_r2 > best_score:
            best_score = mean_r2
            best_params = params
            # Retrain on full data for this best param
            best_model = RandomForestRegressor(**params, random_state=42, n_jobs=-1)
            best_model.fit(X, y, sample_weight=sample_weights)

    logger.info(f"Best RF params: {best_params}, CV R²: {best_score:.4f}")
    return {
        'model_type': 'RandomForest',
        'hyperparameters': best_params,
        'metrics': {'r2_cv': float(best_score)},
        'all_runs': metrics_log
    }

def train_gradient_boosting(X: np.ndarray, y: np.ndarray, sample_weights: np.ndarray,
                            stratification: np.ndarray, config: Dict[str, Any]) -> Dict[str, Any]:
    """Train Gradient Boosting with cross-validation and grid search."""
    logger.info("Training Gradient Boosting...")
    k_folds = config.get('model', {}).get('k_folds', 5)
    max_combos = config.get('model', {}).get('max_grid_search_combinations', 10)

    param_grid = [
        {'n_estimators': 50, 'learning_rate': 0.1, 'max_depth': 3},
        {'n_estimators': 100, 'learning_rate': 0.1, 'max_depth': 3},
        {'n_estimators': 100, 'learning_rate': 0.05, 'max_depth': 4},
    ][:max_combos]

    best_score = -np.inf
    best_params = None
    best_model = None
    metrics_log = []

    skf = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=42)

    for params in param_grid:
        fold_scores = []
        for train_idx, val_idx in skf.split(X, stratification):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            w_train = sample_weights[train_idx]

            model = GradientBoostingRegressor(**params, random_state=42)
            model.fit(X_train, y_train, sample_weight=w_train)

            y_pred = model.predict(X_val)
            r2 = r2_score(y_val, y_pred)
            fold_scores.append(r2)

        mean_r2 = np.mean(fold_scores)
        metrics_log.append({
            'params': params,
            'mean_r2': float(mean_r2),
            'std_r2': float(np.std(fold_scores))
        })

        if mean_r2 > best_score:
            best_score = mean_r2
            best_params = params
            best_model = GradientBoostingRegressor(**params, random_state=42)
            best_model.fit(X, y, sample_weight=sample_weights)

    logger.info(f"Best GB params: {best_params}, CV R²: {best_score:.4f}")
    return {
        'model_type': 'GradientBoosting',
        'hyperparameters': best_params,
        'metrics': {'r2_cv': float(best_score)},
        'all_runs': metrics_log
    }

def train_elastic_net(X: np.ndarray, y: np.ndarray, sample_weights: np.ndarray,
                      stratification: np.ndarray, config: Dict[str, Any]) -> Dict[str, Any]:
    """Train Elastic Net with cross-validation and grid search."""
    logger.info("Training Elastic Net...")
    k_folds = config.get('model', {}).get('k_folds', 5)
    max_combos = config.get('model', {}).get('max_grid_search_combinations', 10)

    param_grid = [
        {'alpha': 0.01, 'l1_ratio': 0.5},
        {'alpha': 0.1, 'l1_ratio': 0.5},
        {'alpha': 0.1, 'l1_ratio': 0.8},
        {'alpha': 1.0, 'l1_ratio': 0.5},
    ][:max_combos]

    best_score = -np.inf
    best_params = None
    best_model = None
    metrics_log = []

    skf = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=42)

    for params in param_grid:
        fold_scores = []
        for train_idx, val_idx in skf.split(X, stratification):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            w_train = sample_weights[train_idx]

            model = ElasticNet(**params, random_state=42, max_iter=5000)
            model.fit(X_train, y_train, sample_weight=w_train)

            y_pred = model.predict(X_val)
            r2 = r2_score(y_val, y_pred)
            fold_scores.append(r2)

        mean_r2 = np.mean(fold_scores)
        metrics_log.append({
            'params': params,
            'mean_r2': float(mean_r2),
            'std_r2': float(np.std(fold_scores))
        })

        if mean_r2 > best_score:
            best_score = mean_r2
            best_params = params
            best_model = ElasticNet(**params, random_state=42, max_iter=5000)
            best_model.fit(X, y, sample_weight=sample_weights)

    logger.info(f"Best EN params: {best_params}, CV R²: {best_score:.4f}")
    return {
        'model_type': 'ElasticNet',
        'hyperparameters': best_params,
        'metrics': {'r2_cv': float(best_score)},
        'all_runs': metrics_log
    }

def save_model_results(results: List[Dict[str, Any]]) -> None:
    """Save model training results to JSON."""
    output_dir = Path(OUTPUT_PATH).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Model results saved to {OUTPUT_PATH}")

def main():
    """Main entry point for model training."""
    logger.info("Starting model training pipeline...")

    # Load config
    config = load_config()

    # Load data
    try:
        df, X, y, y_strat = load_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Compute weights
    try:
        sample_weights = compute_sample_weights(df, config)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Train models
    results = []
    results.append(train_random_forest(X, y, sample_weights, y_strat, config))
    results.append(train_gradient_boosting(X, y, sample_weights, y_strat, config))
    results.append(train_elastic_net(X, y, sample_weights, y_strat, config))

    # Save results
    save_model_results(results)

    logger.info("Model training complete.")

if __name__ == "__main__":
    main()