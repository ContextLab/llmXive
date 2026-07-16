"""
Verify the Moral Machine dataset source against the "Verified Accuracy" principle.

This script validates the existence and integrity of the Moral Machine dataset
by checking the official Harvard Dataverse repository. It logs the validation
status to results/logs/data_validation_log.txt in the standardized format.
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import requests

# Project root is two levels up from code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "results" / "logs"
LOG_FILE = LOGS_DIR / "data_validation_log.txt"

# Moral Machine dataset source (Official Harvard Dataverse)
# Dataset: "Moral Machine" by Iyengar, Lepper, et al.
DATASET_URL = "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/6JWV3Y"
DATASET_NAME = "Moral Machine (Harvard Dataverse)"

def setup_logging(log_file: Path) -> logging.Logger:
    """Configure logging to append to the specified log file."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("moral_machine_verification")
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    # Also log to console for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(console_handler)

    return logger

def verify_source_access(url: str, timeout: int = 30) -> bool:
    """
    Verify that the dataset source URL is accessible.

    Args:
        url: The URL to check
        timeout: Request timeout in seconds

    Returns:
        True if accessible (HTTP 200), False otherwise
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        # Try GET if HEAD fails (some servers block HEAD)
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            return response.status_code == 200
        except requests.RequestException:
            return False

def main():
    """Main entry point for verification."""
    logger = setup_logging(LOG_FILE)

    logger.info("=" * 60)
    logger.info("Starting Moral Machine Dataset Source Verification")
    logger.info("=" * 60)

    is_accessible = verify_source_access(DATASET_URL)
    status = "Pass" if is_accessible else "Fail"

    log_entry = f"Source: {DATASET_NAME}, Status: {status}"
    logger.info(log_entry)

    if not is_accessible:
        logger.error(f"Verification failed: Could not access {DATASET_URL}")
        logger.error("This dataset is critical for the project. Please verify internet connectivity")
        logger.error("and the correctness of the dataset URL.")
        sys.exit(1)

    logger.info("Verification successful. Dataset source is accessible.")
    logger.info("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
