import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

from config import ensure_directories

ERROR_LOG_PATH = None

def setup_error_logger() -> logging.Logger:
    """
    Sets up the error logger for data ingestion errors.
    Creates the log file at data/processed/ingestion_errors.log.
    """
    global ERROR_LOG_PATH
    ensure_directories()
    
    log_dir = Path("data/processed")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    ERROR_LOG_PATH = log_dir / "ingestion_errors.log"
    
    logger = logging.getLogger("ingestion_errors")
    logger.setLevel(logging.ERROR)
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(ERROR_LOG_PATH, mode='w')
    file_handler.setLevel(logging.ERROR)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger

def get_error_log_path() -> Path:
    """Returns the path to the error log file."""
    if ERROR_LOG_PATH is None:
        setup_error_logger()
    return ERROR_LOG_PATH

def log_insufficient_subjects(count: int, required: int = 50) -> None:
    """
    Logs an error message indicating insufficient valid subjects.
    
    Args:
        count: The number of valid subjects found.
        required: The minimum required number of subjects.
    """
    logger = logging.getLogger("ingestion_errors")
    if not logger.handlers:
        setup_error_logger()
    
    message = f"Error: Insufficient valid subjects ({count} found, {required} required)."
    logger.error(message)

def fail_fast_if_insufficient_subjects(count: int, required: int = 50) -> None:
    """
    Checks if the number of valid subjects is below the threshold.
    If so, logs the error and exits with a non-zero exit code.
    
    Args:
        count: The number of valid subjects found.
        required: The minimum required number of subjects.
        
    Raises:
        SystemExit: If count < required, exits with code 1.
    """
    if count < required:
        log_insufficient_subjects(count, required)
        sys.exit(1)

def main() -> None:
    """
    Main entry point for testing the error handling logic.
    This is primarily used for demonstration or unit testing purposes.
    """
    setup_error_logger()
    logger = logging.getLogger("ingestion_errors")
    
    # Example usage: Simulate a failure case
    test_count = 10
    test_required = 50
    
    try:
        fail_fast_if_insufficient_subjects(test_count, test_required)
    except SystemExit as e:
        print(f"SystemExit raised with code: {e.code}")
        print(f"Error log written to: {get_error_log_path()}")

if __name__ == "__main__":
    main()
