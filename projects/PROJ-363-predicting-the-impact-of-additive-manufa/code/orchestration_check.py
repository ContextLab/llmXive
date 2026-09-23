import os
import sys
import json
import logging
from pathlib import Path
from utils import setup_logging

DEGENERATE_FLAG_PATH = "data/processed/degenerate_flag.json"

def check_degenerate_status():
    """
    Checks for the existence of the degenerate dataset flag file.
    
    Returns:
        bool: True if the dataset is degenerate (flag exists), False otherwise.
    """
    if os.path.exists(DEGENERATE_FLAG_PATH):
        try:
            with open(DEGENERATE_FLAG_PATH, 'r') as f:
                flag_data = json.load(f)
                logging.warning(f"Degenerate dataset detected: {flag_data}")
                return True
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error reading degenerate flag file: {e}")
            # If the file exists but is corrupted, treat it as a halt condition to be safe
            return True
    return False

def main():
    """
    Orchestrator entry point to halt pipeline if degenerate dataset is detected.
    
    This script is intended to be run as a gate before subsequent tasks (T016, T017, etc.).
    If `data/processed/degenerate_flag.json` exists, it exits with code 1 and logs a halt message.
    Otherwise, it exits with code 0.
    """
    log_file = os.path.join("results", "logs", "orchestration_check.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = setup_logging(log_file)
    logger.info("Starting orchestration degenerate check...")

    is_degenerate = check_degenerate_status()

    if is_degenerate:
        logger.error("Degenerate Dataset Detected. Halting pipeline execution.")
        # Exit code 1 indicates a graceful stop due to a specific condition, not a crash
        sys.exit(1)
    else:
        logger.info("Dataset is valid. Proceeding with pipeline execution.")
        sys.exit(0)

if __name__ == "__main__":
    main()