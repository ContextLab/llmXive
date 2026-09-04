"""
Module for computing and saving model training metrics.

This module handles the calculation of performance metrics including R², MAE,
feature importances, and the baseline null model R².
"""

import os
import sys
import json
import pickle
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error

# Import from local project modules
from config.config import get_config
from resource_monitor import enforce_resource_limits, ResourceLimitExceeded

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_model(model_path: Path) -> Any:
    """
    Load a pickled model from disk.
    
    Args:
        model_path: Path to the pickled model file.
        
    Returns:
        The loaded model object.
        
    Raises:
        FileNotFoundError: If the model file does not exist.
        pickle.UnpicklingError: If the file cannot be unpickled.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Successfully loaded model from {model_path}")
    return model

def calculate_null_model_r2(y_true: np.ndarray, y_pred_null: np.ndarray) -> float:
    """
    Calculate R² score for a null model (mean prediction).
    
    The null model predicts the mean of the training targets for all samples.
    R² = 1 - (SS_res / SS_tot)
    where SS_res is the sum of squared residuals and SS_tot is the total sum of squares.
    
    Args:
        y_true: True target values.
        y_pred_null: Predictions from the null model (mean of y_true).
        
    Returns:
        R² score of the null model.
    """
    return r2_score(y_true, y_pred_null)

def extract_feature_importances(model: Any, feature_names: List[str]) -> Dict[str, float]:
    """
    Extract feature importances from a tree-based model.
    
    Args:
        model: A fitted tree-based model (e.g., GradientBoostingRegressor).
        feature_names: List of feature names corresponding to the model's features.
        
    Returns:
        Dictionary mapping feature names to their importance values.
        
    Raises:
        AttributeError: If the model does not have a 'feature_importances_' attribute.
    """
    if not hasattr(model, 'feature_importances_'):
        raise AttributeError(
            f"Model type {type(model).__name__} does not support feature importances. "
            "This function expects a tree-based model."
        )
    
    importances = model.feature_importances_
    if len(importances) != len(feature_names):
        raise ValueError(
            f"Mismatch between number of features in model ({len(importances)}) "
            f"and provided feature names ({len(feature_names)})"
        )
    
    return {name: float(imp) for name, imp in zip(feature_names, importances)}

def save_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Save metrics to a JSON file.
    
    Args:
        metrics: Dictionary containing metric values.
        output_path: Path where the JSON file will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics saved to {output_path}")

def compute_and_save_metrics(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Compute all required metrics and save them to a JSON file.
    
    This function calculates:
    - R² score of the trained model
    - MAE of the trained model
    - Feature importances
    - R² score of a null model (mean prediction)
    
    Args:
        model: A fitted regression model.
        X: Feature matrix used for prediction.
        y: True target values.
        feature_names: List of feature names.
        output_path: Path for the output JSON file. If None, defaults to 
                    artifacts/metrics/metrics.json in the project root.
                    
    Returns:
        Dictionary containing all computed metrics.
    """
    # Make predictions
    y_pred = model.predict(X)
    
    # Calculate standard metrics
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    # Calculate null model R² (mean prediction)
    y_mean = np.mean(y)
    y_pred_null = np.full_like(y, y_mean, dtype=float)
    null_model_r2 = calculate_null_model_r2(y, y_pred_null)
    
    # Extract feature importances
    feature_importances = extract_feature_importances(model, feature_names)
    
    # Compile metrics dictionary
    metrics = {
        "R2": float(r2),
        "MAE": float(mae),
        "null_model_r2": float(null_model_r2),
        "feature_importances": feature_importances
    }
    
    # Save to file if path is provided
    if output_path:
        save_metrics(metrics, output_path)
    
    return metrics

@enforce_resource_limits(runtime_limit_h=6, memory_limit_gb=7)
def main() -> int:
    """
    Main entry point for computing and saving model metrics.
    
    Loads the best model from artifacts, computes metrics against the
    prepared data, and saves the results to artifacts/metrics/metrics.json.
    
    Returns:
        0 on success, non-zero on failure.
    """
    try:
        # Get configuration and paths
        config = get_config()
        project_root = get_project_root()
        
        model_path = project_root / "artifacts" / "models" / "best_model.pkl"
        metrics_output_path = project_root / "artifacts" / "metrics" / "metrics.json"
        
        # Load the model
        logger.info(f"Loading model from {model_path}")
        model = load_model(model_path)
        
        # Load prepared data (descriptors and targets)
        # Assuming data is in data/processed/descriptors.csv with a 'Tg' column
        descriptors_path = project_root / "data" / "processed" / "descriptors.csv"
        
        if not descriptors_path.exists():
            logger.error(f"Descriptors file not found: {descriptors_path}")
            return 1
        
        import pandas as pd
        df = pd.read_csv(descriptors_path)
        
        # Identify feature columns (all except 'Tg')
        feature_cols = [col for col in df.columns if col != 'Tg']
        X = df[feature_cols].values
        y = df['Tg'].values
        
        logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features")
        
        # Compute and save metrics
        logger.info("Computing metrics...")
        metrics = compute_and_save_metrics(
            model=model,
            X=X,
            y=y,
            feature_names=feature_cols,
            output_path=metrics_output_path
        )
        
        logger.info("Metrics computation completed successfully")
        logger.info(f"R²: {metrics['R2']:.4f}")
        logger.info(f"MAE: {metrics['MAE']:.4f}")
        logger.info(f"Null Model R²: {metrics['null_model_r2']:.4f}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ResourceLimitExceeded as e:
        logger.error(f"Resource limit exceeded: {e}")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())