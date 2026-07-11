"""
Logging infrastructure for the Hubble Constant Isotropy study.

Provides a centralized logging setup with audit trails for data filtering
operations, ensuring reproducibility and transparency in the analysis pipeline.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Constants for log configuration
LOG_DIR = Path("logs")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = logging.INFO

# Global logger instance cache
_loggers: dict[str, logging.Logger] = {}


def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: Optional[Path] = None,
    console_output: bool = True,
    file_output: bool = True,
) -> None:
    """
    Configure the root logger and ensure the log directory exists.

    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_dir: Directory to store log files. Defaults to project root 'logs'.
        console_output: Whether to log to stderr.
        file_output: Whether to log to a file.
    """
    if log_dir is None:
        log_dir = LOG_DIR

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create a timestamped log file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"pipeline_{timestamp}.log"

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if file_output:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Log startup message
    root_logger.info("Logging infrastructure initialized.")
    root_logger.info(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve or create a named logger.

    Args:
        name: The name of the logger (typically __name__ of the module).

    Returns:
        A configured logger instance.
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        # Ensure it inherits handlers from root
        logger.propagate = True
        _loggers[name] = logger
    return _loggers[name]


def log_data_filtering(
    operation: str,
    input_count: int,
    output_count: int,
    criteria: str,
    logger_name: Optional[str] = None,
) -> None:
    """
    Log a data filtering operation for audit trail purposes.

    This function creates a structured audit log entry that records:
    - The type of filtering operation performed
    - The number of records before filtering
    - The number of records after filtering
    - The specific criteria applied

    Args:
        operation: Name of the filtering operation (e.g., 'redshift_cut', 'quality_flag').
        input_count: Number of records before filtering.
        output_count: Number of records after filtering.
        criteria: Description of the filtering criteria applied.
        logger_name: Optional logger name. Defaults to 'data_audit'.
    """
    logger = get_logger(logger_name or "data_audit")
    removed_count = input_count - output_count
    removal_percentage = (removed_count / input_count * 100) if input_count > 0 else 0.0

    logger.info(
        "AUDIT: Filtering operation '%s' applied. "
        "Criteria: '%s'. "
        "Records: %d -> %d (removed: %d, %.2f%%).",
        operation,
        criteria,
        input_count,
        output_count,
        removed_count,
        removal_percentage,
    )

    if removed_count > 0 and removal_percentage > 10:
        logger.warning(
            "AUDIT WARNING: Filtering '%s' removed >10%% of data (%.2f%%). "
            "Review criteria: '%s'.",
            operation,
            removal_percentage,
            criteria,
        )


def log_error(
    error: Exception,
    context: str,
    logger_name: Optional[str] = None,
) -> None:
    """
    Log an exception with detailed context for debugging.

    Args:
        error: The exception instance.
        context: A string describing the context where the error occurred.
        logger_name: Optional logger name. Defaults to 'error_handler'.
    """
    logger = get_logger(logger_name or "error_handler")
    logger.exception(
        "ERROR in context '%s': %s: %s",
        context,
        type(error).__name__,
        str(error),
    )