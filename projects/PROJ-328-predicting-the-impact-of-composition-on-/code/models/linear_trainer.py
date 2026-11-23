"""
Linear Regression Baseline Trainer for Solder Hardness Prediction.

This module implements a Linear Regression baseline model to predict Vickers
hardness from compositional descriptors. It enforces CPU-only execution as
specified in config_cpu.py and loads pre-computed features from the descriptor
engineering pipeline.

The model serves as a baseline for comparison against the XGBoost model
(T025) to determine if complex non-linear interactions significantly
improve prediction performance.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import joblib

# Project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

# Ensure directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

def load_features_and_target() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load the physical descriptors and target hardness from the cleaned dataset.

    Returns:
        Tuple containing:
            - X (np.ndarray): Feature matrix (descriptors)
            - y (np.ndarray): Target vector (hardness_hv)
            - feature_names (List[str]): List of feature column names
    
    Raises:
        FileNotFoundError: If the required data files are missing.
        ValueError: If the data format is invalid.
    """
    descriptors_path = DATA_PROCESSED_DIR / "descriptors.csv"
    cleaned_data_path = DATA_PROCESSED_DIR / "solder_hardness_cleaned.csv"

    if not descriptors_path.exists():
        raise FileNotFoundError(
            f"Descriptors file not found at {descriptors_path}. "
            "Please ensure T023c (Descriptor Engine) has been run."
        )
    
    if not cleaned_data_path.exists():
        raise FileNotFoundError(
            f"Cleaned data file not found at {cleaned_data_path}. "
            "Please ensure T013 (Data Cleaner) has been run."
        )

    # Load descriptors
    df_desc = pd.read_csv(descriptors_path)
    
    # Load cleaned data to get hardness
    df_clean = pd.read_csv(cleaned_data_path)

    # Merge on a common ID if present, or assume row alignment if IDs are missing
    # The descriptor_engine.py should preserve row order or include an index.
    # Assuming 'index' or 'row_id' exists, otherwise we align by position if counts match.
    if 'index' in df_desc.columns and 'index' in df_clean.columns:
        df_merged = pd.merge(df_desc, df_clean[['index', 'hardness_hv']], on='index')
    elif 'row_id' in df_desc.columns and 'row_id' in df_clean.columns:
        df_merged = pd.merge(df_desc, df_clean[['row_id', 'hardness_hv']], on='row_id')
    else:
        # Fallback: assume strict row alignment if no ID columns found
        if len(df_desc) != len(df_clean):
            raise ValueError(
                f"Row count mismatch between descriptors ({len(df_desc)}) "
                f"and cleaned data ({len(df_clean)}) and no ID column found for merge."
            )
        df_desc['temp_idx'] = range(len(df_desc))
        df_clean['temp_idx'] = range(len(df_clean))
        df_merged = pd.merge(df_desc, df_clean[['temp_idx', 'hardness_hv']], on='temp_idx')
        df_merged.drop(columns=['temp_idx'], inplace=True)

    # Identify feature columns (exclude target and any metadata)
    target_col = 'hardness_hv'
    feature_cols = [col for col in df_merged.columns if col != target_col]
    
    if not feature_cols:
        raise ValueError("No feature columns found in descriptors.csv.")

    X = df_merged[feature_cols].values
    y = df_merged[target_col].values

    # Handle NaNs if any (should be cleaned already, but safety check)
    if np.isnan(X).any() or np.isnan(y).any():
        logger.warning("NaN values detected in data. Dropping rows with NaNs.")
        mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        X = X[mask]
        y = y[mask]

    logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features.")
    return X, y, feature_cols

def train_linear_model(X: np.ndarray, y: np.ndarray) -> LinearRegression:
    """
    Train a Linear Regression model on the provided data.

    Args:
        X (np.ndarray): Feature matrix.
        y (np.ndarray): Target vector.

    Returns:
        LinearRegression: Trained scikit-learn LinearRegression model.
    """
    logger.info("Initializing Linear Regression model with CPU-only config.")
    
    # Import config to ensure CPU enforcement
    from models.config_cpu import get_linear_params
    config = get_linear_params()

    # Initialize model
    model = LinearRegression(
        fit_intercept=config.get('fit_intercept', True),
        n_jobs=config.get('n_jobs', 1)
    )

    logger.info("Fitting Linear Regression model...")
    model.fit(X, y)
    
    logger.info("Model training complete.")
    return model

def evaluate_model(
    model: LinearRegression, 
    X_test: np.ndarray, 
    y_test: np.ndarray
) -> Dict[str, float]:
    """
    Evaluate the trained model on a test set.

    Args:
        model (LinearRegression): Trained model.
        X_test (np.ndarray): Test features.
        y_test (np.ndarray): Test targets.

    Returns:
        Dict[str, float]: Dictionary of metrics (r2, rmse).
    """
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    return {
        "r2": float(r2),
        "rmse": float(rmse),
        "n_test_samples": int(len(y_test))
    }

def save_model_and_results(
    model: LinearRegression,
    metrics: Dict[str, float],
    feature_names: List[str],
    coefficients: np.ndarray,
    intercept: float
) -> str:
    """
    Save the trained model, metrics, and diagnostics to disk.

    Args:
        model (LinearRegression): Trained model.
        metrics (Dict[str, float]): Evaluation metrics.
        feature_names (List[str]): Names of features.
        coefficients (np.ndarray): Model coefficients.
        intercept (float): Model intercept.

    Returns:
        str: Path to the saved model file.
    """
    model_path = MODELS_DIR / "linear_regression_model.joblib"
    metrics_path = MODELS_DIR / "linear_regression_metrics.json"
    diagnostics_path = MODELS_DIR / "linear_regression_diagnostics.json"

    # Save model
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")

    # Save metrics
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    # Save diagnostics (coefficients)
    diag_data = {
        "intercept": float(intercept),
        "coefficients": {
            name: float(coeff) 
            for name, coeff in zip(feature_names, coefficients)
        },
        "feature_names": feature_names
    }
    with open(diagnostics_path, 'w') as f:
        json.dump(diag_data, f, indent=2)
    logger.info(f"Diagnostics saved to {diagnostics_path}")

    return str(model_path)

def main():
    """
    Main entry point for the Linear Regression trainer.
    Orchestrates loading, training, evaluating, and saving.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # 1. Load Data
        X, y, feature_names = load_features_and_target()
        
        # 2. Split Data (70/30 split, fixed seed for reproducibility)
        # Note: T027 handles the full K-Fold CV, this is a single split for baseline
        # reporting and model saving.
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )

        logger.info(f"Train set size: {len(y_train)}, Test set size: {len(y_test)}")

        # 3. Train Model
        model = train_linear_model(X_train, y_train)

        # 4. Evaluate on Test Set
        test_metrics = evaluate_model(model, X_test, y_test)
        logger.info(f"Test R²: {test_metrics['r2']:.4f}, Test RMSE: {test_metrics['rmse']:.4f}")

        # 5. Save Results
        save_model_and_results(
            model, 
            test_metrics, 
            feature_names, 
            model.coef_, 
            model.intercept_
        )

        logger.info("Linear Regression training pipeline completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during training: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
