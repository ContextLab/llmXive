"""
Task T024b: Save model metrics to artifacts/metrics/metrics.json.

This module loads the trained model and training data, calculates:
- R² (Coefficient of Determination)
- MAE (Mean Absolute Error)
- Feature Importances
- Baseline Null Model R² (predicting the mean)

It saves these metrics to artifacts/metrics/metrics.json.
"""
import os
import sys
import json
import pickle
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config.config import get_config
from resource_monitor import enforce_resource_limits, ResourceLimitExceeded
from train import load_prepared_data, get_family_groups

logger = logging.getLogger(__name__)

def load_model(model_path: Path) -> Any:
    """Load the trained model from pickle file."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Loaded model from {model_path}")
    return model

def calculate_null_model_r2(y_true: np.ndarray) -> float:
    """
    Calculate the R² score of a null model that predicts the mean.
    
    R² = 1 - (SS_res / SS_tot)
    For null model: SS_res = SS_tot (since predictions are mean(y)), so R² = 0.
    However, we calculate it explicitly to verify.
    """
    y_mean = np.mean(y_true)
    y_pred_null = np.full_like(y_true, y_mean, dtype=float)
    
    ss_res = np.sum((y_true - y_pred_null) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        return 0.0
    
    r2_null = 1 - (ss_res / ss_tot)
    return r2_null

def extract_feature_importances(model: Any, feature_names: List[str]) -> Dict[str, float]:
    """
    Extract feature importances from the model.
    Handles GradientBoostingRegressor and similar models.
    """
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        return {name: float(imp) for name, imp in zip(feature_names, importances)}
    else:
        logger.warning("Model does not have feature_importances_ attribute")
        return {name: 0.0 for name in feature_names}

def save_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """Save metrics dictionary to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved metrics to {output_path}")

@enforce_resource_limits(runtime_limit_h=6.0, memory_limit_gb=7.0)
def compute_and_save_metrics(
    model_path: Path,
    descriptors_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Main function to compute and save model metrics.
    
    Args:
        model_path: Path to the trained model pickle file
        descriptors_path: Path to the processed descriptors CSV
        output_path: Path where metrics.json will be saved
        
    Returns:
        Dictionary containing the computed metrics
    """
    logger.info(f"Starting metric computation for model: {model_path}")
    
    # Load the model
    model = load_model(model_path)
    
    # Load the prepared data (descriptors and target)
    X, y, feature_names = load_prepared_data(descriptors_path)
    
    # Ensure we have numpy arrays
    if isinstance(X, pd.DataFrame):
        X = X.values
    if isinstance(y, pd.Series):
        y = y.values
    
    # Make predictions
    y_pred = model.predict(X)
    
    # Calculate R²
    r2 = r2_score(y, y_pred)
    
    # Calculate MAE
    mae = mean_absolute_error(y, y_pred)
    
    # Calculate null model R² (baseline)
    null_r2 = calculate_null_model_r2(y)
    
    # Extract feature importances
    feature_importances = extract_feature_importances(model, feature_names)
    
    # Compile metrics
    metrics = {
        "R2": float(r2),
        "MAE": float(mae),
        "null_model_r2": float(null_r2),
        "feature_importances": feature_importances,
        "n_samples": int(len(y)),
        "n_features": int(len(feature_names)),
        "model_type": type(model).__name__
    }
    
    # Save metrics
    save_metrics(metrics, output_path)
    
    logger.info(f"Metrics computed: R²={r2:.4f}, MAE={mae:.4f}, Null R²={null_r2:.4f}")
    logger.info(f"Feature importances: {feature_importances}")
    
    return metrics

def main():
    """Entry point for the metrics computation script."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/metrics_computation.log')
        ]
    )
    
    try:
        # Load configuration
        config = get_config()
        
        # Define paths
        project_root = Path(__file__).resolve().parent.parent
        model_path = project_root / config['model_path']
        descriptors_path = project_root / config['descriptors_path']
        output_path = project_root / config['metrics_output_path']
        
        # Verify input files exist
        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            sys.exit(1)
        
        if not descriptors_path.exists():
            logger.error(f"Descriptors file not found: {descriptors_path}")
            sys.exit(1)
        
        # Compute and save metrics
        metrics = compute_and_save_metrics(model_path, descriptors_path, output_path)
        
        logger.info("Metrics computation completed successfully")
        
    except ResourceLimitExceeded as e:
        logger.error(f"Resource limit exceeded: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during metrics computation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()