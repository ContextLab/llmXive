"""
T029b: Stable Model Fallback Implementation.

This module ensures that `random_forest_model_stable.pkl` exists.
If the stable model is missing (e.g., T029a failed or was skipped),
it copies the baseline model (`random_forest_model.pkl`) to the stable path
and logs a warning.
"""
import os
import shutil
import logging
import sys

# Add project root to path for imports if running as script
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Constants for file paths relative to project root
MODELS_DIR = "data/models"
BASELINE_MODEL = "random_forest_model.pkl"
STABLE_MODEL = "random_forest_model_stable.pkl"

logger = logging.getLogger(__name__)

def ensure_stable_model_exists():
    """
    Checks for the existence of the stable model.
    If missing, copies the baseline model and logs a warning.
    Returns the path to the stable model.
    """
    baseline_path = os.path.join(MODELS_DIR, BASELINE_MODEL)
    stable_path = os.path.join(MODELS_DIR, STABLE_MODEL)

    if os.path.exists(stable_path):
        logger.info(f"Stable model found at {stable_path}. No fallback needed.")
        return stable_path

    if not os.path.exists(baseline_path):
        error_msg = (
            f"Critical Error: Neither stable model ({stable_path}) "
            f"nor baseline model ({baseline_path}) exists. "
            f"Cannot proceed with T029b fallback."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    logger.warning(
        f"Stable model ({stable_path}) not found. "
        f"Copying baseline model ({BASELINE_MODEL}) to stable path as fallback."
    )
    
    # Ensure the directory exists
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Copy the file
    shutil.copy2(baseline_path, stable_path)
    
    logger.info(f"Successfully copied {BASELINE_MODEL} to {STABLE_MODEL}.")
    return stable_path

def run_fallback():
    """
    Entry point for the fallback script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        stable_model_path = ensure_stable_model_exists()
        logger.info(f"Fallback completed successfully. Stable model path: {stable_model_path}")
        return 0
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during fallback: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_fallback())
