import os
import pickle
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_models_dir, ensure_directories

logger = logging.getLogger(__name__)

def save_model(model: Any, model_name: str, model_type: str = "gpr") -> str:
    """
    Save a trained model artifact to the results/models/ directory.

    Args:
        model: The trained sklearn model object (GPR or LinearRegression).
        model_name: The base name for the file (without extension).
        model_type: Type of model for logging purposes ('gpr' or 'linear').

    Returns:
        str: The absolute path to the saved model file.

    Raises:
        FileNotFoundError: If the model is None.
        IOError: If the file cannot be written.
    """
    if model is None:
        raise FileNotFoundError(f"Attempted to save None model for '{model_name}'.")

    models_dir = get_models_dir()
    ensure_directories([models_dir])

    file_path = Path(models_dir) / f"{model_name}.pkl"

    try:
        with open(file_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Successfully saved {model_type} model to: {file_path}")
        return str(file_path)
    except IOError as e:
        logger.error(f"Failed to save model to {file_path}: {e}")
        raise

def save_models(gpr_model: Any, linear_model: Any) -> Dict[str, str]:
    """
    Save both the trained GPR model and the Linear Regression baseline.

    Args:
        gpr_model: The trained GaussianProcessRegressor.
        linear_model: The trained LinearRegression baseline.

    Returns:
        Dict[str, str]: A dictionary mapping model type to the saved file path.
    """
    logger.info("Starting model saving process for GPR and Linear Baseline.")

    gpr_path = save_model(gpr_model, "gpr_model", "GPR")
    linear_path = save_model(linear_model, "linear_regression_baseline", "Linear")

    return {
        "gpr_model_path": gpr_path,
        "linear_baseline_path": linear_path
    }
