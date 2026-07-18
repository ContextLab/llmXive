"""
Train a Random Forest model on the standardized polymer dataset.

Implements runtime fallback logic per FR-003 and Plan Complexity Tracking:
- Default: max_depth=10, n_estimators=100
- If runtime > 60m: reduce max_depth to 6
- If still > 60m (or fails): reduce max_depth to 4

Output:
- artifacts/model.pkl: Trained model
- data/reports/training_metrics.json: R², MAE, runtime, parameters used
- data/processed/feature_matrix.csv: The feature matrix used for training
"""
import os
import sys
import time
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib

# Project imports based on API surface
from utils.logging_config import get_logger
from utils.errors import DataInsufficientError, ConfigurationError
from features.feature_selection import select_features, save_selected_features_list, save_metadata
from ingestion.models import PolymerRecord

# Constants
MAX_RUNTIME_SECONDS = 60 * 60  # 60 minutes
DEFAULT_MAX_DEPTH = 10
FALLBACK_DEPTH_1 = 6
FALLBACK_DEPTH_2 = 4
N_ESTIMATORS = 100
RANDOM_STATE = 42

logger = get_logger(__name__)

def load_feature_matrix() -> pd.DataFrame:
    """Load the feature matrix from the processed data."""
    feature_matrix_path = Path("data/processed/feature_matrix.csv")
    if not feature_matrix_path.exists():
        raise FileNotFoundError(f"Feature matrix not found at {feature_matrix_path}. "
                                "Run feature engineering tasks first.")
    df = pd.read_csv(feature_matrix_path)
    logger.info(f"Loaded feature matrix with shape: {df.shape}")
    return df

def train_with_params(
    X: np.ndarray, 
    y: np.ndarray, 
    max_depth: int, 
    n_estimators: int = N_ESTIMATORS,
    random_state: int = RANDOM_STATE
) -> Tuple[RandomForestRegressor, float, Dict[str, Any]]:
    """
    Train a Random Forest model and return the model, runtime, and metrics.
    
    Returns:
        model: Trained RandomForestRegressor
        runtime: Time taken to train in seconds
        metrics: Dictionary containing R² and MAE on test set
    """
    start_time = time.time()
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    # Initialize and train model
    model = RandomForestRegressor(
        max_depth=max_depth,
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,
        verbose=1
    )
    
    model.fit(X_train, y_train)
    
    runtime = time.time() - start_time
    
    # Evaluate
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    metrics = {
        "r2_score": float(r2),
        "mae": float(mae),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "test_size": len(y_test),
        "train_size": len(y_train)
    }
    
    return model, runtime, metrics

def train_model_with_fallback(
    X: np.ndarray,
    y: np.ndarray
) -> Tuple[RandomForestRegressor, Dict[str, Any], str]:
    """
    Train model with fallback logic based on runtime.
    
    Returns:
        model: The trained model
        summary: Summary of training process including parameters and metrics
        status: "success", "fallback_1", or "fallback_2"
    """
    depths_to_try = [DEFAULT_MAX_DEPTH, FALLBACK_DEPTH_1, FALLBACK_DEPTH_2]
    
    for depth in depths_to_try:
        logger.info(f"Attempting training with max_depth={depth}")
        try:
            model, runtime, metrics = train_with_params(X, y, max_depth=depth)
            
            if runtime <= MAX_RUNTIME_SECONDS:
                logger.info(f"Training completed successfully in {runtime:.2f}s with max_depth={depth}")
                status = "success" if depth == DEFAULT_MAX_DEPTH else f"fallback_{depth}"
                return model, {
                    "runtime_seconds": runtime,
                    "max_depth": depth,
                    "n_estimators": N_ESTIMATORS,
                    "metrics": metrics,
                    "status": status
                }, status
            else:
                logger.warning(f"Training took {runtime:.2f}s (>{MAX_RUNTIME_SECONDS}s), trying fallback depth {depth}")
                # If we exceeded time, try next fallback
                if depth == DEFAULT_MAX_DEPTH:
                    continue
                elif depth == FALLBACK_DEPTH_1:
                    continue
                else:
                    # Final fallback also exceeded time, but we use it anyway
                    logger.warning(f"Final fallback (max_depth={depth}) also exceeded time limit. Using anyway.")
                    return model, {
                        "runtime_seconds": runtime,
                        "max_depth": depth,
                        "n_estimators": N_ESTIMATORS,
                        "metrics": metrics,
                        "status": "timeout_fallback"
                    }, "timeout_fallback"
                    
        except Exception as e:
            logger.error(f"Training failed with max_depth={depth}: {e}")
            if depth == DEFAULT_MAX_DEPTH:
                continue
            elif depth == FALLBACK_DEPTH_1:
                continue
            else:
                raise ConfigurationError(f"All training attempts failed. Last error: {e}")
    
    raise ConfigurationError("Could not train model with any depth configuration")

def save_model(model: RandomForestRegressor, output_path: str) -> None:
    """Save the trained model to disk."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {output_path}")

def save_training_report(summary: Dict[str, Any], output_path: str) -> None:
    """Save training metrics and parameters to JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Training report saved to {output_path}")

def main():
    """Main entry point for model training."""
    logger.info("Starting model training pipeline...")
    
    # Ensure directories exist
    os.makedirs("artifacts", exist_ok=True)
    os.makedirs("data/reports", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    
    # Load feature matrix
    try:
        df = load_feature_matrix()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # Identify target column (assuming 'permeability_barrer' or similar)
    target_col = None
    for col in ['permeability_barrer', 'permeability', 'performance_score']:
        if col in df.columns:
            target_col = col
            break
    
    if target_col is None:
        raise ConfigurationError("Could not find target column in feature matrix. "
                                 "Expected 'permeability_barrer', 'permeability', or 'performance_score'.")
    
    # Prepare features and target
    X = df.drop(columns=[target_col, 'smiles', 'polymer_name', 'polymer_class'])
    y = df[target_col]
    
    # Handle missing values in features
    X = X.fillna(X.median())
    
    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Target column: {target_col}")
    
    # Train model with fallback logic
    try:
        model, summary, status = train_model_with_fallback(X.values, y.values)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise
    
    # Save model
    model_path = "artifacts/model.pkl"
    save_model(model, model_path)
    
    # Save training report
    report_path = "data/reports/training_metrics.json"
    save_training_report(summary, report_path)
    
    # Log results
    logger.info(f"Training complete. Status: {summary['status']}")
    logger.info(f"R² Score: {summary['metrics']['r2_score']:.4f}")
    logger.info(f"MAE: {summary['metrics']['mae']:.4f}")
    logger.info(f"Runtime: {summary['runtime_seconds']:.2f}s")
    logger.info(f"Max depth used: {summary['max_depth']}")
    
    return model, summary

if __name__ == "__main__":
    main()