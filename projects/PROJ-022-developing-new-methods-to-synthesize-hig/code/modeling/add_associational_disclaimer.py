"""
Module to add an explicit associational disclaimer to the trained model metadata.

This fulfills FR-007: "Add explicit disclaimer in model metadata that findings 
are associational, not causal."

The script loads the saved model artifact, updates its metadata dictionary 
with the required disclaimer, and re-saves the artifact.
"""
import os
import sys
import json
import pickle
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import setup_pipeline_logger, get_logger
from utils.errors import PipelineError

# Initialize logger
logger = get_logger(__name__)

MODEL_PATH = "artifacts/model.pkl"
DISCLAIMER_KEY = "disclaimer_associational_not_causal"
DISCLAIMER_TEXT = (
    "DISCLAIMER: The predictive findings and feature importances derived from this model "
    "are strictly associational. They indicate statistical correlations within the training "
    "data and do not establish causal relationships between polymer structural descriptors "
    "and membrane performance metrics. Causal inference requires controlled experimental "
    "validation. This model is intended for hypothesis generation and candidate screening, "
    "not as a substitute for physical experimentation or causal mechanism analysis."
)

def load_model_artifact(path: str) -> dict:
    """Load the model artifact from disk."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model artifact not found at {path}")
    
    with open(path, 'rb') as f:
        model_data = pickle.load(f)
    
    logger.info(f"Successfully loaded model artifact from {path}")
    return model_data

def add_disclaimer(model_data: dict) -> dict:
    """Add the associational disclaimer to the model metadata."""
    if "metadata" not in model_data:
        model_data["metadata"] = {}
    
    model_data["metadata"][DISCLAIMER_KEY] = DISCLAIMER_TEXT
    
    logger.info("Added associational disclaimer to model metadata")
    return model_data

def save_model_artifact(model_data: dict, path: str) -> None:
    """Save the updated model artifact to disk."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'wb') as f:
        pickle.dump(model_data, f)
    
    logger.info(f"Successfully saved updated model artifact to {path}")

def main():
    """Main entry point to add disclaimer to model metadata."""
    logger.info("Starting process to add associational disclaimer to model metadata")
    
    try:
        # Load the existing model
        model_data = load_model_artifact(MODEL_PATH)
        
        # Add the disclaimer
        updated_model_data = add_disclaimer(model_data)
        
        # Save the updated model
        save_model_artifact(updated_model_data, MODEL_PATH)
        
        # Verify the disclaimer was added
        with open(MODEL_PATH, 'rb') as f:
            verify_data = pickle.load(f)
        
        if DISCLAIMER_KEY in verify_data.get("metadata", {}):
            logger.info("Verification successful: Disclaimer is present in saved model.")
            print(f"Disclaimer added successfully. Key: '{DISCLAIMER_KEY}'")
        else:
            raise PipelineError("Verification failed: Disclaimer not found in saved model.")
        
        logger.info("Process completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Model artifact not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error adding disclaimer to model metadata: {e}")
        raise

if __name__ == "__main__":
    main()
