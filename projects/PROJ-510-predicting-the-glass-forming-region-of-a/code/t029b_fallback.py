"""
Task T029b: Stable Model Fallback

Ensures that a valid stable model exists at `data/models/random_forest_model_stable.pkl`.
If the file does not exist (e.g., T029a failed or was skipped), it copies the base model
from `data/models/random_forest_model.pkl` to the stable location and logs a warning.
"""
import os
import shutil
import logging
import sys

# Project root relative to this script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_MODELS_DIR = os.path.join(PROJECT_ROOT, "data", "models")
BASE_MODEL_PATH = os.path.join(DATA_MODELS_DIR, "random_forest_model.pkl")
STABLE_MODEL_PATH = os.path.join(DATA_MODELS_DIR, "random_forest_model_stable.pkl")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_stable_model_exists():
    """
    Checks for the existence of the stable model.
    If missing, copies the base model and logs a warning.
    """
    if not os.path.exists(DATA_MODELS_DIR):
        os.makedirs(DATA_MODELS_DIR)
        logger.info(f"Created missing directory: {DATA_MODELS_DIR}")

    if os.path.exists(STABLE_MODEL_PATH):
        logger.info(f"Stable model already exists at {STABLE_MODEL_PATH}. Skipping fallback.")
        return True

    if not os.path.exists(BASE_MODEL_PATH):
        error_msg = (
            f"CRITICAL FATAL ERROR: Base model not found at {BASE_MODEL_PATH}. "
            "Cannot create stable model fallback. The pipeline cannot proceed without a model."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    logger.warning(
        f"Stable model not found at {STABLE_MODEL_PATH}. "
        f"Copying base model from {BASE_MODEL_PATH} as a fallback."
    )
    
    try:
        shutil.copy2(BASE_MODEL_PATH, STABLE_MODEL_PATH)
        logger.info(f"Successfully copied base model to stable model: {STABLE_MODEL_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to copy base model to stable model: {e}")
        raise

def run_fallback():
    """Entry point for the script."""
    logger.info("Starting Stable Model Fallback (T029b)...")
    try:
        ensure_stable_model_exists()
        logger.info("T029b completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T029b failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_fallback())