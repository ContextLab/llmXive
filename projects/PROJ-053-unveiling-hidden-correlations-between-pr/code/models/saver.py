import os
import pickle
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_models_dir, ensure_directories

logger = logging.getLogger(__name__)

def save_model(model: Any, model_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Save a trained model artifact to the results/models/ directory.
    
    Args:
        model: The trained model object to save.
        model_name: The base name for the file (e.g., 'gpr_model').
        metadata: Optional dictionary of metadata to save alongside the model.
        
    Returns:
        The absolute path to the saved model file.
        
    Raises:
        FileNotFoundError: If the model object is None.
        IOError: If the file cannot be written.
    """
    if model is None:
        raise FileNotFoundError("Cannot save a None model object.")

    models_dir = get_models_dir()
    ensure_directories([models_dir])
    
    file_path = Path(models_dir) / f"{model_name}.pkl"
    
    logger.info(f"Saving model '{model_name}' to {file_path}")
    
    try:
        with open(file_path, 'wb') as f:
            # Save model and metadata together
            artifact = {
                'model': model,
                'metadata': metadata or {}
            }
            pickle.dump(artifact, f)
        logger.info(f"Model saved successfully: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Failed to save model to {file_path}: {e}")
        raise IOError(f"Failed to save model: {e}") from e

def save_models(gpr_model: Any, linear_baseline: Any, 
                gpr_metadata: Optional[Dict[str, Any]] = None,
                linear_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Save both the trained GPR model and the Linear Regression baseline.
    
    Args:
        gpr_model: The trained GaussianProcessRegressor.
        linear_baseline: The trained LinearRegression.
        gpr_metadata: Optional metadata for the GPR model.
        linear_metadata: Optional metadata for the Linear model.
        
    Returns:
        A dictionary mapping model type to the saved file path.
    """
    logger.info("Starting save process for GPR and Linear Baseline models.")
    
    gpr_path = save_model(gpr_model, "gpr_model", gpr_metadata)
    linear_path = save_model(linear_baseline, "linear_baseline", linear_metadata)
    
    return {
        "gpr_model": gpr_path,
        "linear_baseline": linear_path
    }
