"""
Module to handle logging of ingestion warnings for missing or corrupted subjects.
Logs are written to data/processed/ingestion_warnings.log.
"""
import os
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import ensure_directories

WARNING_LOG_PATH: Optional[Path] = None
logger: Optional[logging.Logger] = None


def setup_warning_logger() -> logging.Logger:
    """
    Initializes the warning logger if not already done.
    Returns the logger instance.
    """
    global WARNING_LOG_PATH, logger

    if logger is not None:
        return logger

    # Ensure the processed directory exists
    ensure_directories()

    # Define the log file path
    WARNING_LOG_PATH = Path("data/processed/ingestion_warnings.log")

    # Create a new logger
    logger = logging.getLogger("ingestion_warnings")
    logger.setLevel(logging.WARNING)

    # Remove any existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(WARNING_LOG_PATH, mode='w')
    file_handler.setLevel(logging.WARNING)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

    # Also log to stderr for immediate visibility during execution
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_warning_log_path() -> Path:
    """
    Returns the path to the warning log file.
    Ensures the logger is set up first.
    """
    setup_warning_logger()
    if WARNING_LOG_PATH is None:
        raise RuntimeError("Warning log path not initialized.")
    return WARNING_LOG_PATH


def log_missing_subject(subject_id: str, reason: str = "Subject directory or data files missing.") -> None:
    """
    Logs a warning that a subject is missing.
    """
    if logger is None:
        setup_warning_logger()
    if logger:
        logger.warning(f"MISSING_SUBJECT: Subject ID '{subject_id}' - {reason}")


def log_corrupted_subject(subject_id: str, reason: str = "Data integrity check failed or file corrupted.") -> None:
    """
    Logs a warning that a subject is corrupted.
    """
    if logger is None:
        setup_warning_logger()
    if logger:
        logger.warning(f"CORRUPTED_SUBJECT: Subject ID '{subject_id}' - {reason}")


def log_download_failure(subject_id: str, reason: str = "Download failed due to network or server error.") -> None:
    """
    Logs a warning that a subject download failed.
    """
    if logger is None:
        setup_warning_logger()
    if logger:
        logger.warning(f"DOWNLOAD_FAILURE: Subject ID '{subject_id}' - {reason}")


def main() -> None:
    """
    Main entry point for testing the warning logger.
    This function demonstrates the logging capabilities.
    """
    print("Initializing warning logger...")
    log_path = get_warning_log_path()
    print(f"Warning log will be written to: {log_path}")

    # Simulate some warnings
    log_missing_subject("100101", "Directory not found in OpenNeuro.")
    log_corrupted_subject("100201", "NIfTI header checksum mismatch.")
    log_download_failure("100301", "Connection timeout after 30s.")

    print("Warning logging test complete. Check data/processed/ingestion_warnings.log")


if __name__ == "__main__":
    main()
