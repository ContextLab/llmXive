"""
Logging infrastructure for the pupil dilation research pipeline.

This module initializes logging to write to code/logs/preprocess.log
and initializes results/quality_report.csv with required headers.
"""
import logging
import os
import csv
from pathlib import Path
from typing import Optional

# Project root relative to this file (code/)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
LOGS_DIR = PROJECT_ROOT / "logs"
RESULTS_DIR = PROJECT_ROOT / "results"

# Output paths
LOG_FILE_PATH = LOGS_DIR / "preprocess.log"
QUALITY_REPORT_PATH = RESULTS_DIR / "quality_report.csv"

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure logging to write to code/logs/preprocess.log.
    
    Args:
        log_level: Optional log level string (e.g., 'DEBUG', 'INFO').
                  If None, defaults to 'INFO'.
    
    Returns:
        The root logger with configured handlers.
    
    Raises:
        FileNotFoundError: If the logs directory cannot be created.
    """
    # Determine log level
    level = getattr(logging, log_level.upper() if log_level else "INFO")
    
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Add handler to root logger
    root_logger.addHandler(file_handler)
    
    # Also add a stream handler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(stream_handler)
    
    return root_logger


def initialize_quality_report() -> None:
    """
    Initialize results/quality_report.csv with headers [exclusion_type, count].
    
    If the file already exists, this function checks if headers are present.
    If headers are missing, it overwrites the file with the correct headers.
    
    Raises:
        FileNotFoundError: If the results directory cannot be created.
        PermissionError: If the file cannot be written.
    """
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Define required headers
    headers = ["exclusion_type", "count"]
    
    # Check if file exists
    if QUALITY_REPORT_PATH.exists():
        try:
            with open(QUALITY_REPORT_PATH, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                first_row = next(reader, None)
                
                # Verify headers match
                if first_row != headers:
                    # Overwrite with correct headers
                    with open(QUALITY_REPORT_PATH, 'w', newline='', encoding='utf-8') as wf:
                        writer = csv.writer(wf)
                        writer.writerow(headers)
        except Exception as e:
            # If we can't read, overwrite
            with open(QUALITY_REPORT_PATH, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    else:
        # Create new file with headers
        with open(QUALITY_REPORT_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)


def write_quality_entry(exclusion_type: str, count: int) -> None:
    """
    Append a quality report entry to results/quality_report.csv.
    
    Args:
        exclusion_type: The type of exclusion (e.g., "blink", "missing_data").
        count: The count of exclusions for this type.
    
    Raises:
        FileNotFoundError: If the results directory does not exist.
        PermissionError: If the file cannot be written.
    """
    # Ensure file is initialized with headers
    if not QUALITY_REPORT_PATH.exists():
        initialize_quality_report()
    
    # Append entry
    with open(QUALITY_REPORT_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([exclusion_type, count])


def get_logger(name: str = "pupil_pipeline") -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The name for the logger.
    
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)


def main() -> None:
    """
    Main function to initialize logging and quality report.
    
    This function is designed to be called at the start of the pipeline
    to ensure all logging and reporting infrastructure is ready.
    """
    # Setup logging
    logger = setup_logging()
    logger.info("Logging infrastructure initialized.")
    
    # Initialize quality report
    initialize_quality_report()
    logger.info(f"Quality report initialized at: {QUALITY_REPORT_PATH}")
    
    # Verify files exist
    if LOG_FILE_PATH.exists():
        logger.info(f"Log file exists: {LOG_FILE_PATH}")
    else:
        logger.warning(f"Log file not found: {LOG_FILE_PATH}")
    
    if QUALITY_REPORT_PATH.exists():
        logger.info(f"Quality report exists: {QUALITY_REPORT_PATH}")
        # Verify headers
        with open(QUALITY_REPORT_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers == ["exclusion_type", "count"]:
                logger.info("Quality report headers verified.")
            else:
                logger.warning(f"Quality report headers unexpected: {headers}")
    else:
        logger.warning(f"Quality report not found: {QUALITY_REPORT_PATH}")


if __name__ == "__main__":
    main()
