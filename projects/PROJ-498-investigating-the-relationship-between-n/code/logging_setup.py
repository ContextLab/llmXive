import logging
import os
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional

# Constants for paths (relative to project root)
LOG_FILE_PATH = "logs/processing.log"
EXCLUSIONS_FILE_PATH = "data/exclusions.csv"
EXCLUSIONS_COLUMNS = ["subject_id", "reason", "timestamp"]

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logger(name: str = "research_pipeline") -> logging.Logger:
    """
    Configures and returns a logger that writes to logs/processing.log.
    Ensures the logs directory exists.
    """
    global _logger
    if _logger is not None:
        return _logger

    log_path = Path(LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if called multiple times
    if not _logger.handlers:
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)

    return _logger

def get_logger() -> logging.Logger:
    """
    Returns the configured logger instance.
    Initializes it if it hasn't been initialized yet.
    """
    return setup_logger()

class ExclusionTracker:
    """
    Handles writing exclusion records to data/exclusions.csv.
    Ensures the file header exists and appends rows atomically.
    """
    
    def __init__(self, file_path: str = EXCLUSIONS_FILE_PATH):
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Creates the CSV file with headers if it does not exist."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=EXCLUSIONS_COLUMNS)
                writer.writeheader()

    def log_exclusion(self, subject_id: str, reason: str):
        """
        Appends a new exclusion record to the CSV.
        
        Args:
            subject_id: The identifier of the subject being excluded.
            reason: The reason for exclusion (e.g., "insufficient trials").
        """
        timestamp = datetime.now().isoformat()
        row = {
            "subject_id": subject_id,
            "reason": reason,
            "timestamp": timestamp
        }
        
        with open(self.file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=EXCLUSIONS_COLUMNS)
            writer.writerow(row)

        # Log to the main logger as well
        logger = get_logger()
        logger.warning(f"Subject {subject_id} excluded: {reason}")

    def get_excluded_subjects(self) -> list:
        """
        Reads the CSV and returns a list of excluded subject IDs.
        """
        if not self.file_path.exists():
            return []
        
        excluded = []
        with open(self.file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                excluded.append(row['subject_id'])
        return excluded

def initialize_logging_and_tracking():
    """
    Convenience function to initialize both the logger and the exclusion tracker.
    Ensures directories exist and files are ready for writing.
    """
    setup_logger()
    tracker = ExclusionTracker()
    return tracker

def main():
    """
    Test entry point to verify logging and exclusion tracking work correctly.
    """
    # Initialize
    tracker = initialize_logging_and_tracking()
    logger = get_logger()

    logger.info("Logging infrastructure test started.")
    
    # Test exclusion logging
    tracker.log_exclusion("sub-001", "insufficient trials")
    tracker.log_exclusion("sub-002", "excessive artifact removal")
    
    logger.info("Exclusion tests completed.")
    
    # Verify file existence
    if Path(EXCLUSIONS_FILE_PATH).exists():
        print(f"Success: {EXCLUSIONS_FILE_PATH} created.")
        with open(EXCLUSIONS_FILE_PATH, 'r') as f:
            print(f.read())
    else:
        print("Error: Exclusions file not created.")

    if Path(LOG_FILE_PATH).exists():
        print(f"Success: {LOG_FILE_PATH} created.")
    else:
        print("Error: Log file not created.")

if __name__ == "__main__":
    main()