"""
Model Serialization Module (T031)

Implements model serialization to the `models/` directory with metadata
including hyperparameters and cross-validation scores.
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import numpy as np
import pandas as pd

# Import from project utilities
from utils.config import get_env_var
from utils.io import compute_sha256

# Setup logging
logger = logging.getLogger(__name__)

# Constants
MODELS_DIR = Path("models")
METADATA_FILE = "model_metadata.json"

def ensure_models_dir():
    """Ensure the models directory exists."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured models directory exists at {MODELS_DIR}")

def serialize_model(
    model,
    model_name: str,
    hyperparameters: Dict[str, Any],
    cv_scores: Dict[str, List[float]],
    feature_names: Optional[List[str]] = None,
    output_dir: Optional[Path] = None
) -> str:
    """
    Serialize a trained model and its metadata to disk.
    
    Args:
        model: The trained scikit-learn model object.
        model_name: A unique name for the model (e.g., 'linear_regression', 'random_forest').
        hyperparameters: Dictionary of hyperparameters used for training.
        cv_scores: Dictionary mapping metric names (e.g., 'r2', 'mae') to lists of fold scores.
        feature_names: Optional list of feature names used in the model.
        output_dir: Optional path to output directory (defaults to MODELS_DIR).
        
    Returns:
        Path to the saved model file.
    """
    if output_dir is None:
        output_dir = MODELS_DIR
        
    ensure_models_dir()
    
    # Sanitize model name for filename
    safe_name = model_name.replace(" ", "_").lower()
    model_filename = f"{safe_name}.pkl"
    model_path = output_dir / model_filename
    
    # Serialize the model
    logger.info(f"Serializing model '{model_name}' to {model_path}")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
        
    # Prepare metadata
    metadata = {
        "model_name": model_name,
        "model_type": type(model).__name__,
        "hyperparameters": hyperparameters,
        "cv_scores": cv_scores,
        "feature_names": feature_names,
        "serialized_at": datetime.utcnow().isoformat(),
        "model_path": str(model_path),
        "checksum": compute_sha256(str(model_path))
    }
    
    # Save metadata
    metadata_path = output_dir / METADATA_FILE
    
    # Load existing metadata if present to append
    existing_metadata = []
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_metadata = data
                elif isinstance(data, dict):
                    # Handle case where file might have single entry previously
                    existing_metadata = [data]
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing metadata from {metadata_path}: {e}. Starting new list.")
            existing_metadata = []
    
    existing_metadata.append(metadata)
    
    with open(metadata_path, 'w') as f:
        json.dump(existing_metadata, f, indent=2)
        
    logger.info(f"Saved model metadata to {metadata_path}")
    logger.info(f"Model '{model_name}' serialized successfully with checksum {metadata['checksum']}")
    
    return str(model_path)

def load_model(model_path: str):
    """
    Load a serialized model from disk.
    
    Args:
        model_path: Path to the .pkl file.
        
    Returns:
        The deserialized model object.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
        
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
        
    return model

def load_latest_metadata() -> List[Dict[str, Any]]:
    """
    Load the latest model metadata from the models directory.
    
    Returns:
        List of metadata dictionaries for all serialized models.
    """
    metadata_path = MODELS_DIR / METADATA_FILE
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}. Returning empty list.")
        return []
        
    with open(metadata_path, 'r') as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata file: {e}")
            return []

def main():
    """
    Main entry point for testing serialization functionality.
    This script is intended to be called by the training pipeline (T025/T029).
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage simulation (would be called from train.py)
    logger.info("Serialization module initialized. Ready to serialize models.")
    
    # Verify directories
    ensure_models_dir()
    
    # Check if metadata file exists
    if (MODELS_DIR / METADATA_FILE).exists():
        logger.info("Existing metadata found.")
        metadata = load_latest_metadata()
        logger.info(f"Found {len(metadata)} serialized model(s) in metadata.")
        for entry in metadata:
            logger.info(f"  - {entry.get('model_name', 'Unknown')}: {entry.get('model_type', 'Unknown')}")
    else:
        logger.info("No existing metadata found. Ready for first serialization.")

if __name__ == "__main__":
    main()