"""
Train Random Forest and Gradient Boosting models for corrosion potential prediction.

Uses GroupKFold (k=5) indices to prevent alloy leakage.
CPU-only implementation using scikit-learn.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.metrics import r2_score, mean_squared_error
from joblib import dump

# Project imports
from utils.config import (
    get_config,
    set_random_seed,
    get_processed_data_path,
    get_split_indices_path,
    get_model_results_path,
    get_path,
)
from utils.logging import get_logger, log_message
from utils.exceptions import DataInsufficientError

logger = get_logger(__name__)

# Constants
RANDOM_STATE = 42
N_FOLDS = 5
MODEL_TYPES = {
    "random_forest": RandomForestRegressor,
    "gradient_boosting": GradientBoostingRegressor,
}

def load_split_indices() -> Dict[str, Any]:
    """Load pre-computed GroupKFold split indices."""
    split_path = get_split_indices_path()
    if not split_path.exists():
        raise FileNotFoundError(f"Split indices not found at {split_path}. Run split.py first.")
    
    with open(split_path, 'r') as f:
        return json.load(f)

def load_processed_data() -> pd.DataFrame:
    """Load the preprocessed dataset."""
    data_path = get_processed_data_path()
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run preprocess.py first.")
    
    logger.info(f"Loading processed data from {data_path}")
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} records")
    return df

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare feature matrix X, target y, and group labels.
    
    Features: All numeric columns except target and group identifier.
    Target: 'corrosion_potential_mv'
    Group: 'specific_alloy_designation_id'
    """
    target_col = "corrosion_potential_mv"
    group_col = "specific_alloy_designation_id"
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset")
    if group_col not in df.columns:
        raise ValueError(f"Group column '{group_col}' not found in dataset")
    
    # Identify feature columns (numeric, excluding target and group)
    feature_cols = [
        col for col in df.select_dtypes(include=[np.number]).columns
        if col not in [target_col, group_col]
    ]
    
    if len(feature_cols) == 0:
        raise DataInsufficientError("No feature columns found in dataset")
    
    logger.info(f"Using {len(feature_cols)} features: {feature_cols[:5]}...")
    
    X = df[feature_cols].values
    y = df[target_col].values
    groups = df[group_col].values
    
    return X, y, groups, feature_cols

def train_model(
    model_name: str,
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    feature_cols: List[str],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Train a single model using GroupKFold cross-validation.
    
    Returns metrics aggregated across folds.
    """
    logger.info(f"Training {model_name} model...")
    start_time = time.time()
    
    # Get model class and parameters
    model_class = MODEL_TYPES[model_name]
    model_params = config.get("models", {}).get(model_name, {})
    
    # Ensure random_state is set
    model_params["random_state"] = RANDOM_STATE
    
    model = model_class(**model_params)
    
    # Setup GroupKFold
    gkf = GroupKFold(n_splits=N_FOLDS)
    
    # Store fold results
    fold_r2 = []
    fold_rmse = []
    fold_times = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        fold_start = time.time()
        model.fit(X_train, y_train)
        fold_time = time.time() - fold_start
        fold_times.append(fold_time)
        
        y_pred = model.predict(X_test)
        
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        fold_r2.append(r2)
        fold_rmse.append(rmse)
        
        logger.info(f"  Fold {fold_idx + 1}/{N_FOLDS}: R²={r2:.4f}, RMSE={rmse:.4f} mV")
    
    # Aggregate metrics
    avg_r2 = np.mean(fold_r2)
    std_r2 = np.std(fold_r2)
    avg_rmse = np.mean(fold_rmse)
    std_rmse = np.std(fold_rmse)
    avg_time = np.mean(fold_times)
    
    total_time = time.time() - start_time
    
    result = {
        "model_name": model_name,
        "metrics": {
            "r2_mean": float(avg_r2),
            "r2_std": float(std_r2),
            "rmse_mean_mV": float(avg_rmse),
            "rmse_std_mV": float(std_rmse),
            "train_time_seconds": float(total_time),
            "avg_fold_time_seconds": float(avg_time),
        },
        "fold_metrics": [
            {"fold": i + 1, "r2": float(r2), "rmse_mV": float(rmse)}
            for i, (r2, rmse) in enumerate(zip(fold_r2, fold_rmse))
        ],
        "hyperparameters": model_params,
        "n_samples": len(y),
        "n_features": len(feature_cols),
        "n_folds": N_FOLDS,
    }
    
    logger.info(f"{model_name} completed in {total_time:.2f}s. Avg R²={avg_r2:.4f}±{std_r2:.4f}")
    
    return result

def save_model_artifact(model, model_name: str, feature_cols: List[str], config: Dict[str, Any]):
    """Save the trained model and metadata."""
    output_dir = get_path("data", "processed", "models")
    os.makedirs(output_dir, exist_ok=True)
    
    model_path = os.path.join(output_dir, f"{model_name}_model.joblib")
    logger.info(f"Saving model to {model_path}")
    
    dump({
        "model": model,
        "feature_cols": feature_cols,
        "model_name": model_name,
        "random_state": RANDOM_STATE,
    }, model_path)

def train_all_models() -> Dict[str, Any]:
    """
    Main training pipeline: load data, train all models, save results.
    """
    # Load configuration
    config = get_config()
    set_random_seed(RANDOM_STATE)
    
    logger.info("Starting model training pipeline...")
    logger.info(f"Using random_state={RANDOM_STATE}, n_folds={N_FOLDS}")
    
    # Load data
    df = load_processed_data()
    X, y, groups, feature_cols = prepare_features(df)
    
    # Verify GroupKFold integrity (check from split validation)
    split_path = get_split_indices_path()
    with open(split_path, 'r') as f:
        split_data = json.load(f)
    
    if not split_data.get("validation", {}).get("is_valid", False):
        logger.warning("Split validation failed. Proceeding with caution.")
    
    # Train models
    all_results = {
        "training_config": {
            "random_state": RANDOM_STATE,
            "n_folds": N_FOLDS,
            "n_samples": len(y),
            "n_features": len(feature_cols),
            "features": feature_cols,
        },
        "models": {},
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    for model_name in MODEL_TYPES.keys():
        result = train_model(model_name, X, y, groups, feature_cols, config)
        all_results["models"][model_name] = result
        
        # Train final model on full data for saving
        final_model_params = config.get("models", {}).get(model_name, {})
        final_model_params["random_state"] = RANDOM_STATE
        final_model = MODEL_TYPES[model_name](**final_model_params)
        final_model.fit(X, y)
        save_model_artifact(final_model, model_name, feature_cols, config)
    
    # Determine best model
    model_scores = {
        name: data["metrics"]["r2_mean"] 
        for name, data in all_results["models"].items()
    }
    best_model = max(model_scores, key=model_scores.get)
    all_results["best_model"] = best_model
    all_results["best_model_score"] = model_scores[best_model]
    
    # Save results
    results_path = get_model_results_path()
    os.makedirs(results_path.parent, exist_ok=True)
    
    with open(results_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Training complete. Results saved to {results_path}")
    logger.info(f"Best model: {best_model} (R²={model_scores[best_model]:.4f})")
    
    return all_results

def main():
    """Entry point for training script."""
    try:
        results = train_all_models()
        logger.info("Training pipeline completed successfully.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        log_message("ERROR", str(e), level=logging.ERROR)
        return 1
    except DataInsufficientError as e:
        logger.error(f"Insufficient data for training: {e}")
        log_message("ERROR", f"DataInsufficientError: {e}", level=logging.ERROR)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during training: {e}", exc_info=True)
        log_message("ERROR", f"Unexpected error: {e}", level=logging.ERROR)
        return 1

if __name__ == "__main__":
    sys.exit(main())