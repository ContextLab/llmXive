"""
Error handling module for data ingestion failures.

Implements FR-010: Fail fast with non-zero exit code and error message
"Error: Insufficient valid subjects (<50)" if <50 valid subjects found.
Logs errors to data/processed/ingestion_errors.log.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

from config import ensure_directories
from data_ingestion import validate_session_distinctness, download_subject_data
from ingestion_warnings import setup_warning_logger, get_warning_log_path


# Minimum number of valid subjects required
MIN_VALID_SUBJECTS = 50


def setup_error_logger(log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Setup and return a logger for ingestion errors.
    
    Args:
        log_dir: Directory for log files. Defaults to data/processed/.
    
    Returns:
        Configured logger instance.
    """
    if log_dir is None:
        log_dir = Path("data/processed")
    
    ensure_directories(log_dir)
    
    log_path = log_dir / "ingestion_errors.log"
    
    logger = logging.getLogger("ingestion_errors")
    logger.setLevel(logging.ERROR)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setLevel(logging.ERROR)
    
    # Format: timestamp - level - message
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger


def get_error_log_path(log_dir: Optional[Path] = None) -> Path:
    """
    Get the path to the error log file.
    
    Args:
        log_dir: Directory for log files. Defaults to data/processed/.
    
    Returns:
        Path to the error log file.
    """
    if log_dir is None:
        log_dir = Path("data/processed")
    return log_dir / "ingestion_errors.log"


def log_insufficient_subjects(
    logger: logging.Logger,
    valid_count: int,
    required_count: int = MIN_VALID_SUBJECTS
) -> None:
    """
    Log an error when insufficient valid subjects are found.
    
    Args:
        logger: Logger instance to write to.
        valid_count: Number of valid subjects found.
        required_count: Minimum required subjects (default: 50).
    """
    error_msg = f"Error: Insufficient valid subjects ({valid_count} < {required_count})"
    logger.error(error_msg)


def fail_fast_if_insufficient_subjects(
    valid_subject_ids: List[str],
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Check if we have enough valid subjects and fail fast if not.
    
    This implements FR-010: Fail fast with non-zero exit code and error message
    "Error: Insufficient valid subjects (<50)" if <50 valid subjects found.
    
    Args:
        valid_subject_ids: List of valid subject IDs.
        logger: Logger instance. If None, creates a new one.
    
    Raises:
        SystemExit: With code 1 if insufficient subjects are found.
    """
    valid_count = len(valid_subject_ids)
    
    if logger is None:
        logger = setup_error_logger()
    
    if valid_count < MIN_VALID_SUBJECTS:
        log_insufficient_subjects(logger, valid_count, MIN_VALID_SUBJECTS)
        error_msg = f"Error: Insufficient valid subjects ({valid_count} < {MIN_VALID_SUBJECTS})"
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # Success - log the count
    logger.info(f"Valid subject count ({valid_count}) meets minimum requirement ({MIN_VALID_SUBJECTS})")


def main() -> None:
    """
    Main entry point for error checking.
    
    This function is intended to be called after data ingestion and validation
    to ensure we have enough valid subjects before proceeding.
    """
    # This is a utility module - actual checking happens in data_ingestion.py
    # This main() is for standalone testing/debugging
    print("ingestion_errors module loaded successfully")
    print(f"Minimum valid subjects required: {MIN_VALID_SUBJECTS}")


if __name__ == "__main__":
    main()