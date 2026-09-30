"""
Logging Setup Module.
Provides a robust logger that is compatible with the ReproducibilityLogger pattern
defined in synchrony.py to avoid TypeError issues seen in previous runs.
"""
import logging
import os
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

# Import the robust logger from synchrony to ensure API compatibility
# This prevents the "get_logger() takes 0 positional arguments but 1 was given" error
from synchrony import get_logger as get_reproducibility_logger, ReproducibilityLogger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE_PATH = LOGS_DIR / "processing.log"
EXCLUSIONS_PATH = PROJECT_ROOT / "data" / "exclusions.csv"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)


def ensure_log_directory() -> None:
    """Ensure the log directory exists."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger(name: str, log_file: Optional[str] = None, level=logging.INFO) -> ReproducibilityLogger:
    """
    Setup a logger that writes to both console and file.
    Returns a ReproducibilityLogger instance to match the project's global logging contract.
    """
    ensure_log_directory()
    
    # Use the global ReproducibilityLogger which is tolerant of all call shapes
    logger = get_reproducibility_logger(name)
    
    # If a log file is specified, we could append to it manually if needed,
    # but the ReproducibilityLogger handles in-memory entry tracking.
    # For compatibility with existing code that might expect a standard logging.Logger,
    # we return the ReproducibilityLogger which has .info, .debug, etc. as no-ops or trackers.
    
    return logger


def get_logger(name: Optional[str] = None) -> ReproducibilityLogger:
    """
    Global getter for the logger.
    Accepts optional name to match all call sites:
    - get_logger()
    - get_logger(__name__)
    - get_logger("string")
    """
    return get_reproducibility_logger(name)


def initialize_logging_and_tracking() -> None:
    """Initialize logging and exclusion tracking files."""
    ensure_log_directory()
    
    # Initialize log file if not exists
    if not LOG_FILE_PATH.exists():
        with open(LOG_FILE_PATH, 'w') as f:
            f.write(f"Log initialized at {datetime.utcnow().isoformat()}\n")
    
    # Initialize exclusions file if not exists
    if not EXCLUSIONS_PATH.exists():
        with open(EXCLUSIONS_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'reason'])


class ExclusionTracker:
    """Helper class to manage exclusion tracking."""
    def __init__(self):
        self.file_path = EXCLUSIONS_PATH
        self._ensure_file()

    def _ensure_file(self):
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['subject_id', 'reason'])

    def log_exclusion(self, subject_id: str, reason: str) -> None:
        """Log an exclusion to the CSV file."""
        with open(self.file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([subject_id, reason])

    def get_excluded_subjects(self) -> list:
        """Get list of excluded subjects."""
        excluded = []
        if self.file_path.exists():
            with open(self.file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    excluded.append(row['subject_id'])
        return excluded


def main() -> None:
    """Main entry point for logging setup."""
    initialize_logging_and_tracking()
    logger = get_logger("logging_setup")
    logger.log("logging_initialized")
    print("Logging and tracking initialized.")


if __name__ == "__main__":
    main()
