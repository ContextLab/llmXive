import logging
import os
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"
EXCLUSIONS_PATH = DATA_DIR / "exclusions.csv"

def ensure_log_directory():
    """Ensure the logs directory exists."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str = "processing") -> logging.Logger:
    """
    Set up a logger that writes to both console and file.
    """
    ensure_log_directory()
    log_file = LOGS_DIR / "processing.log"
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def get_logger() -> logging.Logger:
    """Get the main processing logger."""
    return setup_logger("processing")

def initialize_logging_and_tracking():
    """Initialize logging and ensure tracking files exist."""
    ensure_log_directory()
    # Ensure exclusions file exists with headers
    if not EXCLUSIONS_PATH.exists():
        with open(EXCLUSIONS_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'reason'])
    # Ensure metrics directory exists
    (DATA_DIR / "metrics").mkdir(parents=True, exist_ok=True)

class ExclusionTracker:
    """Utility to log exclusions to data/exclusions.csv."""
    
    @staticmethod
    def log_exclusion(subject_id: str, reason: str):
        """Log an exclusion to the CSV file."""
        with open(EXCLUSIONS_PATH, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([subject_id, reason])
        
        logger = get_logger()
        logger.info(f"Excluded subject {subject_id}: {reason}")

def main():
    """Entry point for testing logging setup."""
    initialize_logging_and_tracking()
    logger = get_logger()
    logger.info("Logging system initialized.")
    ExclusionTracker.log_exclusion("test-subject", "test reason")

if __name__ == "__main__":
    main()
