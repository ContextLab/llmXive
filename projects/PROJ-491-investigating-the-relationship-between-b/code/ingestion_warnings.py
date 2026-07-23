"""
Handles logging of warnings for corrupted or missing subjects during data ingestion.
This module ensures that any subject failing validation (missing files, corrupted NIfTI)
is logged to `data/processed/ingestion_warnings.log` and does not crash the pipeline.
"""
import os
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import ensure_directories

# Constants
LOG_FILE_NAME = "ingestion_warnings.log"
LOG_DIR = Path("data/processed")

def setup_warning_logger(log_path: Optional[Path] = None) -> logging.Logger:
    """
    Sets up a dedicated logger for ingestion warnings.
    The logger writes to both the console (WARNING level) and a file.
    
    Args:
        log_path: Optional path to the log file. Defaults to data/processed/ingestion_warnings.log.
    
    Returns:
        A configured logging.Logger instance.
    """
    if log_path is None:
        log_path = LOG_DIR / LOG_FILE_NAME
    
    ensure_directories()
    
    logger = logging.getLogger("ingestion_warnings")
    logger.setLevel(logging.WARNING)
    
    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # File handler
    fh = logging.FileHandler(log_path, mode='a')
    fh.setLevel(logging.WARNING)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def log_missing_subject(subject_id: str, reason: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Logs a warning for a subject that is missing required files.
    
    Args:
        subject_id: The HCP subject ID.
        reason: Description of why the subject is missing (e.g., "REST file not found").
        logger: Optional logger instance. If None, uses the default setup.
    """
    if logger is None:
        logger = setup_warning_logger()
    
    msg = f"MISSING_SUBJECT: Subject {subject_id} - {reason}"
    logger.warning(msg)

def log_corrupted_subject(subject_id: str, error_details: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Logs a warning for a subject with corrupted data files.
    
    Args:
        subject_id: The HCP subject ID.
        error_details: Details of the corruption (e.g., "NIfTI header checksum mismatch").
        logger: Optional logger instance. If None, uses the default setup.
    """
    if logger is None:
        logger = setup_warning_logger()
    
    msg = f"CORRUPTED_SUBJECT: Subject {subject_id} - {error_details}"
    logger.warning(msg)

def log_download_failure(subject_id: str, error_msg: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Logs a warning for a subject where data download failed.
    
    Args:
        subject_id: The HCP subject ID.
        error_msg: The error message from the download attempt.
        logger: Optional logger instance. If None, uses the default setup.
    """
    if logger is None:
        logger = setup_warning_logger()
    
    msg = f"DOWNLOAD_FAILURE: Subject {subject_id} - {error_msg}"
    logger.warning(msg)

def get_warning_log_path() -> Path:
    """Returns the path to the ingestion warnings log file."""
    return LOG_DIR / LOG_FILE_NAME

def main() -> None:
    """
    Main entry point for testing the warning logger.
    This function demonstrates logging different types of ingestion failures.
    """
    logger = setup_warning_logger()
    
    # Simulate logging scenarios
    log_missing_subject("100106", "REST_NIFTI file not found in OpenNeuro archive", logger)
    log_corrupted_subject("100208", "NIfTI file header indicates invalid dimensions", logger)
    log_download_failure("100309", "Connection timeout after 30s", logger)
    
    print(f"\nWarnings logged to: {get_warning_log_path()}")

if __name__ == "__main__":
    main()