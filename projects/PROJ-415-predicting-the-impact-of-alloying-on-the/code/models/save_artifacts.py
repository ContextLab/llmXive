import os
import json
import pickle
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from config import MODELS_DIR
from utils.logging import get_logger

logger = get_logger(__name__)

def save_model_to_pickle(model: Any, filename: str) -> None:
    """Save a trained model to a pickle file in the models directory."""
    model_path = Path(MODELS_DIR) / filename
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")

def save_linear_coefficients(coef: float, intercept: float, p_value: float) -> None:
    """
    Save Linear Regression coefficients to models/linear_coef.json.
    
    Args:
        coef: The size_mismatch coefficient
        intercept: The intercept of the linear model
        p_value: The p-value associated with the coefficient
    """
    output_path = Path(MODELS_DIR) / "linear_coef.json"
    
    data = {
        "coef": float(coef),
        "intercept": float(intercept),
        "p_value": float(p_value)
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Linear coefficients saved to {output_path}")

def aggregate_metrics(
    rf_r2: Optional[float] = None,
    rf_rmse: Optional[float] = None,
    rf_mae: Optional[float] = None,
    gb_r2: Optional[float] = None,
    gb_rmse: Optional[float] = None,
    gb_mae: Optional[float] = None,
    mean_r2: Optional[float] = None
) -> None:
    """
    Aggregate model metrics into models/metrics.json.
    
    This function reads existing metrics (if any) and updates/merges
    the provided metrics, then saves the result.
    """
    metrics_path = Path(MODELS_DIR) / "metrics.json"
    
    # Load existing metrics if present
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
    else:
        metrics = {}
    
    # Update with new metrics
    if rf_r2 is not None:
        metrics['rf_r2'] = float(rf_r2)
    if rf_rmse is not None:
        metrics['rf_rmse'] = float(rf_rmse)
    if rf_mae is not None:
        metrics['rf_mae'] = float(rf_mae)
    if gb_r2 is not None:
        metrics['gb_r2'] = float(gb_r2)
    if gb_rmse is not None:
        metrics['gb_rmse'] = float(gb_rmse)
    if gb_mae is not None:
        metrics['gb_mae'] = float(gb_mae)
    if mean_r2 is not None:
        metrics['mean_r2'] = float(mean_r2)
    
    # Save updated metrics
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics aggregated and saved to {metrics_path}")

def main():
    """
    Main entry point for saving artifacts.
    
    This script is expected to be called by the training pipeline
    after models are trained and evaluated. It handles:
    1. Saving Linear Regression coefficients to linear_coef.json
    2. Aggregating metrics from RF, GB, and Mean Predictor into metrics.json
    
    Usage:
        python code/models/save_artifacts.py
    """
    # Ensure models directory exists
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    logger.info("Starting artifact saving process...")
    
    # Example usage (this would be called with real values from training.py):
    # save_linear_coefficients(coef=0.5, intercept=1.0, p_value=0.001)
    # aggregate_metrics(rf_r2=0.85, rf_rmse=0.12, rf_mae=0.09, ...)
    
    logger.info("Artifact saving process completed.")

if __name__ == "__main__":
    main()
