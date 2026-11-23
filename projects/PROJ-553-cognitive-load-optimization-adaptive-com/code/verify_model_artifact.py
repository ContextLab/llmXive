"""
Verify model artifact: Assert model file exists and size is within limits.

This script verifies the output of T015 (train_load_model.py).
It checks for the existence of either:
- data/processed/load_model.pkl (high confidence, r >= 0.6)
- data/processed/load_model_low_confidence.pkl (low confidence, r < 0.6)

It asserts the file size is <= 500 MB.
It raises an error if the file is missing or too large.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MAX_SIZE_MB = 500
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

HIGH_CONF_FILE = PROCESSED_DIR / "load_model.pkl"
LOW_CONF_FILE = PROCESSED_DIR / "load_model_low_confidence.pkl"

def verify_model_artifact() -> bool:
    """
    Verify that a valid model artifact exists and meets size constraints.
    
    Returns:
        True if a valid model is found and verified.
        Raises FileNotFoundError or ValueError if verification fails.
    """
    found_file: Optional[Path] = None
    
    # Check for high confidence model first
    if HIGH_CONF_FILE.exists():
        found_file = HIGH_CONF_FILE
        logger.info(f"Found high-confidence model: {found_file}")
    elif LOW_CONF_FILE.exists():
        found_file = LOW_CONF_FILE
        logger.info(f"Found low-confidence model: {found_file}")
    else:
        error_msg = (
            "Model artifact missing: Neither 'data/processed/load_model.pkl' "
            "nor 'data/processed/load_model_low_confidence.pkl' exists. "
            "Please ensure T015 (train_load_model.py) has run successfully."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Verify file size
    file_size_bytes = found_file.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    logger.info(f"Model file size: {file_size_mb:.2f} MB (limit: {MAX_SIZE_MB} MB)")
    
    if file_size_bytes > MAX_SIZE_BYTES:
        error_msg = (
            f"Model artifact too large: {found_file.name} is {file_size_mb:.2f} MB. "
            f"Maximum allowed size is {MAX_SIZE_MB} MB."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Model artifact verification PASSED: {found_file.name} is valid.")
    return True

def main():
    """Entry point for the verification script."""
    try:
        verify_model_artifact()
        logger.info("Verification successful. Exiting with code 0.")
        sys.exit(0)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Verification FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
