import logging
import os
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "processing.log"
EXCLUSIONS_FILE = Path("data/exclusions.csv")

logger_instance: Optional[logging.Logger] = None

def ensure_log_directory():
    """Ensure the logs directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str = "pipeline_logger") -> logging.Logger:
    """
    Configure and return the main pipeline logger.
    Writes to logs/processing.log and console.
    """
    global logger_instance
    if logger_instance is not None:
        return logger_instance

    ensure_log_directory()

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    logger_instance = logger
    return logger

def get_logger() -> logging.Logger:
    """Get the configured logger instance."""
    return setup_logger()

class ExclusionTracker:
    """Helper class to manage exclusion logging."""
    
    @staticmethod
    def ensure_exclusions_file_exists():
        """Create the exclusions CSV file with headers if it doesn't exist."""
        if not EXCLUSIONS_FILE.exists():
            EXCLUSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(EXCLUSIONS_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['subject_id', 'reason'])

    @staticmethod
    def log_exclusion(subject_id: str, reason: str):
        """Log an exclusion to the CSV file."""
        ExclusionTracker.ensure_exclusions_file_exists()
        with open(EXCLUSIONS_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([subject_id, reason])

def initialize_logging_and_tracking():
    """Initialize the logger and ensure exclusion file exists."""
    get_logger()
    ExclusionTracker.ensure_exclusions_file_exists()

def main():
    """Test logging setup."""
    logger = get_logger()
    logger.info("Logging initialized successfully.")
    logger.debug("Debug message test.")
    logger.warning("Warning message test.")
    ExclusionTracker.log_exclusion("TEST_SUBJ", "test_reason")
    print(f"Exclusions logged to {EXCLUSIONS_FILE}")

if __name__ == "__main__":
    main()
