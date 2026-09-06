"""
Orchestration Check Module.

Implements the logic to verify the existence of the degenerate flag file
and halt the pipeline execution gracefully if a degenerate dataset is detected.
"""
import os
import sys
import json
import logging
from pathlib import Path

from utils import setup_logging

# Configuration constants
DEGENERATE_FLAG_PATH = "data/processed/degenerate_flag.json"
DEGENERATE_STATUS_KEY = "status"
DEGENERATE_VALUE = "degenerate"
DEGENERATE_REASON_KEY = "reason"

logger = logging.getLogger(__name__)

def check_degenerate_status(flag_path: str = DEGENERATE_FLAG_PATH) -> bool:
    """
    Checks if the degenerate dataset flag file exists and contains the correct status.
    
    Args:
        flag_path: Path to the degenerate flag JSON file.
        
    Returns:
        True if the dataset is flagged as degenerate, False otherwise.
        
    Raises:
        RuntimeError: If the flag file exists but is malformed or indicates a degenerate state.
    """
    path = Path(flag_path)
    
    if not path.exists():
        logger.info("Degenerate flag file not found. Proceeding with pipeline.")
        return False
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"Degenerate flag file exists but is not valid JSON: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Failed to read degenerate flag file: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    status = data.get(DEGENERATE_STATUS_KEY)
    reason = data.get(DEGENERATE_REASON_KEY, "Unknown reason")
    
    if status == DEGENERATE_VALUE:
        error_msg = f"Degenerate dataset detected. Reason: {reason}. Halting pipeline."
        logger.error(error_msg)
        # Log the specific reason for transparency
        logger.error("Pipeline halted due to zero variance in target variable.")
        return True
    
    logger.info(f"Flag file exists but status is '{status}'. Proceeding with pipeline.")
    return False

def main():
    """
    Main entry point for the orchestration check.
    
    Checks for the degenerate flag. If found, logs the error and exits with code 1.
    If not found, logs success and exits with code 0.
    """
    setup_logging()
    logger.info("Starting orchestration degenerate check...")
    
    try:
        is_degenerate = check_degenerate_status()
        
        if is_degenerate:
            logger.error("Pipeline HALTED due to degenerate dataset.")
            sys.exit(1)
        else:
            logger.info("Orchestration check passed. Pipeline can proceed.")
            sys.exit(0)
            
    except RuntimeError as e:
        logger.error(f"Critical error during orchestration check: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during orchestration check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()