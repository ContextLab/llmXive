import os
import json
import pickle
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from config import MODELS_DIR
from utils.logging import get_logger

logger = get_logger(__name__)

def save_model_to_pickle(model, filename: str):
    """Save a trained model to a pickle file."""
    path = MODELS_DIR / filename
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {path}")

def save_linear_coefficients(coefficients: Dict[str, Any], filename: str):
    """Save linear regression coefficients to a JSON file."""
    path = MODELS_DIR / filename
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(coefficients, f, indent=2)
    logger.info(f"Coefficients saved to {path}")

def main():
    """Placeholder for artifact saving logic if called directly."""
    logger.info("Artifact saving module loaded.")

if __name__ == "__main__":
    main()
