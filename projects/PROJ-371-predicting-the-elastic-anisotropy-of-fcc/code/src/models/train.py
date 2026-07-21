"""
Train regression models for elastic anisotropy prediction using Leave-One-Element-Out (LOEO) CV.

This module implements the training pipeline for User Story 2, specifically
deviating from the spec's random 80/20 split to use LOEO to prevent chemical
similarity leakage (Constitution Principle VII).

Models trained:
- Random Forest Regressor
- Gradient Boosting Regressor
- Linear Regression

All training is CPU-only (no GPU/CUDA).
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error

# Import project utilities
from src.utils.config import get_config, get_path, set_random_seed, get_seed
from src.utils.logging import get_logger, log_info, log_warning, log_error, log_success

# Constants
MODEL_TYPES = {
    "random_forest": RandomForestRegressor,
    "gradient_boosting": GradientBoostingRegressor,
    "linear_regression": LinearRegression
}

# Default hyperparameters for CPU-only execution
DEFAULT_HYPERPARAMETERS = {
    "random_forest": {
        "n_estimators": 100,
        "max_depth": 10,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "random_state": 42,
        "n_jobs": -1  # Use all CPU cores
    },
    "gradient_boosting": {
        "n_estimators": 100,
        "max_depth": 5,
        "learning_rate": 0.1,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "random_state": 42
    },
    "linear_regression": {}
}

logger = get_logger(__name__)

def load_processed_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the processed elastic anisotropy dataset.
    
    Args:
        data_path: Path to the processed CSV file. If None, uses config default.
        
    Returns:
        DataFrame with features and target variable.
        
    Raises:
        FileNotFoundError: If the data file doesn't exist.
    """
    if data_path is None:
        config = get_config()
        data_path = get_path("processed_elastic_anisotropy_csv")
    
    if not data_path.exists():
        log_error(f"Processed data file not found: {data_path}")
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
    
    log_info(f"Loading processed data from: {data_path}")
    df = pd.read_csv(data_path)
    
    # Validate required columns
    required_cols = ["C11", "C12", "C44", "A1"]
    feature_cols = [col for col in df.columns if col not in required_cols + ["material_id", "element"]]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        log_error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    log_success(f"Loaded {len(df)} samples with {len(feature_cols)} features")
    return df, feature_cols

def prepare_loeo_data(df: pd.DataFrame, feature_cols: List[str]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare data for Leave-One-Element-Out cross-validation.
    
    Args:
        df: DataFrame with features and target.
        feature_cols: List of feature column names.
        
    Returns:
        Tuple of (X, y, groups) where groups are element identifiers.
    """
    X = df[feature_cols].values
    y = df["A1"].values
    groups = df["element"].values  # Group by element for LOEO
    
    log_info(f"Prepared data: X shape {X.shape}, y shape {y.shape}, unique elements: {len(np.unique(groups))}")
    return X, y, groups

def train_single_model(
    model_type: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    hyperparams: Optional[Dict[str, Any]] = None
):
    """
    Train a single model instance.
    
    Args:
        model_type: Name of the model type.
        X_train: Training features.
        y_train: Training targets.
        hyperparams: Optional hyperparameter overrides.
        
    Returns:
        Trained model instance.
    """
    model_class = MODEL_TYPES.get(model_type)
    if model_class is None:
        raise ValueError(f"Unknown model type: {model_type}")
    
    params = DEFAULT_HYPERPARAMETERS.get(model_type, {}).copy()
    if hyperparams:
        params.update(hyperparams)
    
    log_info(f"Training {model_type} with params: {params}")
    model = model_class(**params)
    model.fit(X_train, y_train)
    
    return model

def evaluate_model(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_type: str
) -> Dict[str, float]:
    """
    Evaluate a trained model and return metrics.
    
    Args:
        model: Trained model instance.
        X_test: Test features.
        y_test: Test targets.
        model_type: Name of the model type.
        
    Returns:
        Dictionary with R², MAE, and RMSE metrics.
    """
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = root_mean_squared_error(y_test, y_pred)
    
    metrics = {
        "model_type": model_type,
        "r2": float(r2),
        "mae": float(mae),
        "rmse": float(rmse),
        "n_test_samples": int(len(y_test))
    }
    
    log_info(f"{model_type} evaluation: R²={r2:.4f}, MAE={mae:.4f}, RMSE={rmse:.4f}")
    return metrics

def run_loeo_cross_validation(
    df: pd.DataFrame,
    feature_cols: List[str],
    model_types: Optional[List[str]] = None,
    hyperparams: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Run Leave-One-Element-Out cross-validation for all specified models.
    
    This implements the chemical similarity leakage mitigation strategy
    by ensuring no element appears in both training and test sets.
    
    Args:
        df: Processed DataFrame with features and target.
        feature_cols: List of feature column names.
        model_types: List of model types to train. Defaults to all.
        hyperparams: Optional hyperparameter overrides per model type.
        
    Returns:
        Dictionary containing all training results and metrics.
    """
    if model_types is None:
        model_types = list(MODEL_TYPES.keys())
    
    if hyperparams is None:
        hyperparams = {}
    
    X, y, groups = prepare_loeo_data(df, feature_cols)
    
    logo = LeaveOneGroupOut()
    
    results = {
        "config": {
            "cv_method": "Leave-One-Element-Out",
            "n_elements": int(len(np.unique(groups))),
            "n_samples": int(len(y)),
            "feature_count": len(feature_cols),
            "models_trained": model_types,
            "random_seed": get_seed()
        },
        "model_results": {}
    }
    
    log_info(f"Starting LOEO CV with {len(np.unique(groups))} elements across {len(y)} samples")
    
    for model_type in model_types:
        log_info(f"{'='*50}")
        log_info(f"Training {model_type} with LOEO CV")
        log_info(f"{'='*50}")
        
        model_metrics = []
        fold_models = []  # Store models if needed later
        
        for fold_idx, (train_idx, test_idx) in enumerate(logo.split(X, y, groups)):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            train_elements = groups[train_idx]
            test_elements = groups[test_idx]
            
            # Verify no element overlap
            train_el_set = set(train_elements)
            test_el_set = set(test_elements)
            overlap = train_el_set.intersection(test_el_set)
            
            if overlap:
                log_error(f"Element overlap detected in fold {fold_idx}: {overlap}")
                raise ValueError(f"LOEO violation: elements {overlap} appear in both train and test")
            
            # Train model
            fold_hyperparams = hyperparams.get(model_type, None)
            model = train_single_model(model_type, X_train, y_train, fold_hyperparams)
            
            # Evaluate
            metrics = evaluate_model(model, X_test, y_test, model_type)
            metrics["fold"] = fold_idx
            model_metrics.append(metrics)
            
            log_debug(f"Fold {fold_idx}: {len(train_idx)} train, {len(test_idx)} test samples")
        
        # Aggregate metrics
        avg_metrics = {
            "model_type": model_type,
            "avg_r2": float(np.mean([m["r2"] for m in model_metrics])),
            "std_r2": float(np.std([m["r2"] for m in model_metrics])),
            "avg_mae": float(np.mean([m["mae"] for m in model_metrics])),
            "std_mae": float(np.std([m["mae"] for m in model_metrics])),
            "avg_rmse": float(np.mean([m["rmse"] for m in model_metrics])),
            "std_rmse": float(np.std([m["rmse"] for m in model_metrics])),
            "n_folds": len(model_metrics),
            "fold_metrics": model_metrics
        }
        
        results["model_results"][model_type] = avg_metrics
        log_success(f"{model_type} LOEO CV complete: R²={avg_metrics['avg_r2']:.4f}±{avg_metrics['std_r2']:.4f}")
    
    return results

def save_results(results: Dict[str, Any], output_path: Optional[Path] = None):
    """
    Save training results to JSON file.
    
    Args:
        results: Dictionary of training results.
        output_path: Path to save results. If None, uses config default.
    """
    if output_path is None:
        config = get_config()
        output_path = get_path("model_metrics_json")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    log_success(f"Training results saved to: {output_path}")

def main():
    """
    Main entry point for model training pipeline.
    """
    log_info("Starting model training pipeline (T020)")
    
    # Set random seed for reproducibility
    set_random_seed(42)
    
    try:
        # Load data
        df, feature_cols = load_processed_data()
        
        # Run LOEO cross-validation
        results = run_loeo_cross_validation(df, feature_cols)
        
        # Save results
        save_results(results)
        
        log_success("Model training pipeline completed successfully")
        return 0
        
    except FileNotFoundError as e:
        log_error(f"Data file not found: {e}")
        log_info("Please ensure the data pipeline (T015) has been run first to generate data/processed/elastic_anisotropy.csv")
        return 1
    except Exception as e:
        log_error(f"Training pipeline failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
