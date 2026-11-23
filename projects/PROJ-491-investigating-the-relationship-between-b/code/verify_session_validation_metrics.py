"""
Task T013d: Verify session_validation_metrics.json exists and contains valid keys.

This script checks for the existence of data/processed/session_validation_metrics.json
and validates that it contains the required keys: pass_rate, total_subjects, valid_subjects.
It exits with code 0 if valid, and code 1 if missing or invalid.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

METRICS_FILE_PATH = Path("data/processed/session_validation_metrics.json")
REQUIRED_KEYS = {"pass_rate", "total_subjects", "valid_subjects"}

def verify_metrics_file():
    """
    Verify the metrics file exists and contains the required keys.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not METRICS_FILE_PATH.exists():
        logger.error(f"Metrics file not found: {METRICS_FILE_PATH}")
        return False

    try:
        with open(METRICS_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in metrics file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading metrics file: {e}")
        return False

    missing_keys = REQUIRED_KEYS - set(data.keys())
    if missing_keys:
        logger.error(f"Missing required keys in metrics file: {missing_keys}")
        logger.error(f"Found keys: {set(data.keys())}")
        return False

    # Validate types
    if not isinstance(data.get("pass_rate"), (int, float)):
        logger.error(f"pass_rate must be a number, got {type(data.get('pass_rate'))}")
        return False
    if not isinstance(data.get("total_subjects"), int):
        logger.error(f"total_subjects must be an integer, got {type(data.get('total_subjects'))}")
        return False
    if not isinstance(data.get("valid_subjects"), int):
        logger.error(f"valid_subjects must be an integer, got {type(data.get('valid_subjects'))}")
        return False

    logger.info(f"Metrics file verified successfully: {METRICS_FILE_PATH}")
    logger.info(f"Content: {data}")
    return True

def main():
    """Entry point for the verification script."""
    logger.info("Starting session validation metrics verification (Task T013d)...")
    if verify_metrics_file():
        logger.info("Verification PASSED.")
        sys.exit(0)
    else:
        logger.error("Verification FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
