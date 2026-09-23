"""
XGBoost Model Training with Grid Search and CPU-Only Execution.

This module implements the training of an XGBoost regressor for predicting
Vickers hardness from solder alloy composition descriptors. It enforces
CPU-only execution via configuration from `config_cpu.py` and performs
a limited grid search (<= 10 combinations) to optimize hyperparameters.

The script reads prepared features from `data/processed/descriptors.csv`
and `data/processed/clr_features.csv` (if applicable, though physical descriptors
are used for the model input as per spec), and the target from
`data/processed/solder_hardness_cleaned.csv`.

It outputs the best model, training metrics, and cross-validation results
to `data/processed/` and `models/`.
"""
import os
import sys
import logging
import json
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import GridSearchCV, train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Project imports
from seed import init_reproducibility
from utils.logging_config import get_logger
from models.config_cpu import get_xgboost_params, get_cpu_config
from models.entities import create_descriptor_from_composition

# Initialize logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "data" / "outputs"

# Ensure directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

def load_features_and_target() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the physical descriptors (features) and the target hardness values.

    Returns:
        Tuple[pd.DataFrame, pd.Series]: Features matrix (X) and target vector (y).
    """
    # Load descriptors (physical properties calculated from raw composition)
    # This corresponds to T023c output
    descriptors_path = DATA_PROCESSED_DIR / "descriptors.csv"
    if not descriptors_path.exists():
        raise FileNotFoundError(f"Descriptors file not found at {descriptors_path}. "
                                "Ensure T023c has been executed.")

    df_desc = pd.read_csv(descriptors_path)

    # Load target (hardness)
    # This corresponds to T013 output
    cleaned_path = DATA_PROCESSED_DIR / "solder_hardness_cleaned.csv"
    if not cleaned_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found at {cleaned_path}. "
                                "Ensure T013 has been executed.")

    df_clean = pd.read_csv(cleaned_path)

    # Merge on a common identifier if present, or assume row alignment if IDs are missing
    # Assuming 'sample_id' or similar exists, otherwise we rely on row order if IDs are not present.
    # Based on typical data models, we expect an ID column. Let's check for 'sample_id' or 'id'.
    id_col = None
    for col in ['sample_id', 'id', 'composition_id']:
        if col in df_desc.columns and col in df_clean.columns:
            id_col = col
            break

    if id_col:
        df_merged = pd.merge(df_desc, df_clean[[id_col, 'hardness_hv']], on=id_col)
        logger.info(f"Merged data on ID column: {id_col}. Rows: {len(df_merged)}")
    else:
        # Fallback to row alignment if no ID found (risky but sometimes necessary)
        if len(df_desc) != len(df_clean):
            raise ValueError("Row counts mismatch between descriptors and cleaned data, and no ID column found.")
        df_merged = df_desc.copy()
        df_merged['hardness_hv'] = df_clean['hardness_hv']
        logger.warning("No ID column found. Assuming row alignment between descriptors and cleaned data.")

    # Drop rows with missing target
    df_merged = df_merged.dropna(subset=['hardness_hv'])

    # Identify feature columns (exclude target and ID)
    feature_cols = [col for col in df_merged.columns if col not in ['hardness_hv', id_col]]
    X = df_merged[feature_cols]
    y = df_merged['hardness_hv']

    logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features.")
    logger.info(f"Features: {feature_cols}")

    return X, y

def run_grid_search(X: pd.DataFrame, y: pd.Series) -> Tuple[xgb.XGBRegressor, Dict[str, Any]]:
    """
    Perform a grid search over XGBoost hyperparameters using CPU-only settings.

    The grid is limited to <= 10 combinations as per requirements.

    Args:
        X (pd.DataFrame): Feature matrix.
        y (pd.Series): Target vector.

    Returns:
        Tuple[xgb.XGBRegressor, Dict[str, Any]]: Best model and best parameters.
    """
    # Split data for final evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Base parameters from CPU config
    base_params = get_xgboost_params()
    logger.info(f"Base XGBoost parameters (CPU enforced): {base_params}")

    # Define a small grid for hyperparameter tuning
    # We vary 'max_depth' and 'learning_rate' to keep combinations <= 10
    param_grid = {
        'max_depth': [3, 6],          # 2 values
        'learning_rate': [0.05, 0.1, 0.2]  # 3 values
        # Total combinations: 2 * 3 = 6 (well under 10)
    }

    # Initialize the model with base params
    # Note: We pass base_params as init, but GridSearchCV will override specific keys
    base_model = xgb.XGBRegressor(**base_params)

    # Grid Search
    logger.info("Starting Grid Search with <= 10 combinations...")
    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=5,
        scoring='r2',
        n_jobs=1,  # Enforce single-threaded for CPU stability in CI
        verbose=1
    )

    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    best_score = grid_search.best_score_

    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best CV R² score: {best_score:.4f}")

    # Evaluate on test set
    y_pred = best_model.predict(X_test)
    test_r2 = r2_score(y_test, y_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    logger.info(f"Test Set R²: {test_r2:.4f}")
    logger.info(f"Test Set RMSE: {test_rmse:.4f}")

    results = {
        "best_params": best_params,
        "best_cv_r2": float(best_score),
        "test_r2": float(test_r2),
        "test_rmse": float(test_rmse),
        "grid_combinations": len(param_grid['max_depth']) * len(param_grid['learning_rate'])
    }

    return best_model, results

def save_model_and_results(model: xgb.XGBRegressor, results: Dict[str, Any]):
    """
    Save the trained model and training metrics to disk.

    Args:
        model (xgb.XGBRegressor): The trained model.
        results (Dict[str, Any]): Training metrics and parameters.
    """
    # Save model
    model_path = MODELS_DIR / "xgboost_hardness_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")

    # Save metrics
    metrics_path = DATA_PROCESSED_DIR / "xgboost_training_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Training metrics saved to {metrics_path}")

def main():
    """
    Main entry point for XGBoost training.
    """
    logger.info("Starting XGBoost Training (Task T025)...")
    
    # Initialize reproducibility
    init_reproducibility(seed=42)

    try:
        # 1. Load Data
        X, y = load_features_and_target()
        
        if len(X) < 10:
            logger.error("Insufficient data for training. Need at least 10 samples.")
            sys.exit(1)

        # 2. Run Grid Search
        best_model, results = run_grid_search(X, y)

        # 3. Save Outputs
        save_model_and_results(best_model, results)

        logger.info("XGBoost Training completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main() or 0)
