"""
Model Saving Module for llmXive Project PROJ-084

Handles the serialization of trained model artifacts, hyperparameters,
and associated metadata to the project's results directory.
"""
import json
import logging
import pickle
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/model_saving.log')
    ]
)
logger = logging.getLogger(__name__)

# Ensure the output directory exists
def ensure_dir(dir_path: Path) -> None:
    """
    Creates the directory if it does not exist.
    
    Args:
        dir_path: The Path object representing the directory to create.
    
    Raises:
        OSError: If the directory cannot be created.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {dir_path}")
    except OSError as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        raise

def save_model_artifacts(
    model: Any,
    model_type: str,
    hyperparameters: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> Path:
    """
    Saves a trained model and its metadata to disk.
    
    This function serializes the model object using pickle and saves
    a JSON file containing the hyperparameters and metadata.
    
    Args:
        model: The trained sklearn model object (e.g., RandomForestRegressor, SVC).
        model_type: A string identifier for the model (e.g., 'random_forest', 'svm').
        hyperparameters: A dictionary of the hyperparameters used for training.
        output_dir: Optional Path to the output directory. Defaults to 'data/results/best_models'.
    
    Returns:
        Path: The path to the directory where artifacts were saved.
    
    Raises:
        TypeError: If the model cannot be pickled.
        IOError: If files cannot be written.
    """
    if output_dir is None:
        output_dir = Path("data/results/best_models")
    
    ensure_dir(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model_type = model_type.replace(" ", "_").lower()
    
    # Define file paths
    model_file = output_dir / f"{safe_model_type}_model_{timestamp}.pkl"
    meta_file = output_dir / f"{safe_model_type}_meta_{timestamp}.json"
    
    # Save the model
    try:
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model saved to {model_file}")
    except TypeError as e:
        logger.error(f"Failed to pickle model: {e}")
        raise
    except IOError as e:
        logger.error(f"Failed to write model file: {e}")
        raise
    
    # Save metadata
    metadata = {
        "model_type": model_type,
        "hyperparameters": hyperparameters,
        "saved_at": timestamp,
        "model_file_name": model_file.name
    }
    
    try:
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=4)
        logger.info(f"Metadata saved to {meta_file}")
    except IOError as e:
        logger.error(f"Failed to write metadata file: {e}")
        raise
    
    return output_dir

def main():
    """
    Main entry point for the save_models script.
    
    This is a demonstration function that would typically be called by
    the training pipeline (train.py) to persist the best model found.
    In a real execution flow, this would be imported and called with
    actual model objects from train.py.
    
    For the purpose of this task implementation, it demonstrates the
    logic required to save a model artifact.
    """
    # This script is intended to be imported by train.py.
    # If run directly, it logs its purpose.
    logger.info("save_models module loaded. Ready to save artifacts.")
    logger.info("Usage: from modeling.save_models import save_model_artifacts")

if __name__ == "__main__":
    main()