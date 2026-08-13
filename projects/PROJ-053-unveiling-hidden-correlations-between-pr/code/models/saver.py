import os
import pickle
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_models_dir, ensure_directories

logger = logging.getLogger(__name__)

def save_model(model: Any, model_name: str, directory: Optional[Path] = None) -> Path:
    """
    Save a trained model to disk using pickle.

    Args:
        model: The trained model object to save.
        model_name: The filename for the saved model (e.g., 'gpr_model.pkl').
        directory: Optional specific directory. If None, uses the project's models dir.

    Returns:
        Path to the saved file.
    """
    if directory is None:
        directory = get_models_dir()
    
    ensure_directories()
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
    
    file_path = directory / model_name
    
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model saved successfully to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save model to {file_path}: {e}")
        raise
    
    return file_path

def save_models(gpr_model: Any, linear_model: Any, 
                gpr_name: str = "gpr_model.pkl", 
                linear_name: str = "linear_regression_baseline.pkl") -> Dict[str, Path]:
    """
    Save both the trained GPR model and the Linear Regression baseline.

    Args:
        gpr_model: The trained GaussianProcessRegressor instance.
        linear_model: The trained LinearRegression instance.
        gpr_name: Filename for the GPR model.
        linear_name: Filename for the linear model.

    Returns:
        Dictionary mapping model type to saved file path.
    """
    ensure_directories()
    models_dir = get_models_dir()
    
    if not models_dir.exists():
        models_dir.mkdir(parents=True, exist_ok=True)
    
    gpr_path = save_model(gpr_model, gpr_name, models_dir)
    linear_path = save_model(linear_model, linear_name, models_dir)
    
    logger.info(f"Both models saved to {models_dir}")
    
    return {
        "gpr": gpr_path,
        "linear_baseline": linear_path
    }
