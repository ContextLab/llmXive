"""
Logging infrastructure for the Hubble Constant Isotropy project.

Provides centralized logging configuration, audit trails for data filtering,
and error handling utilities.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# Default log format including timestamp, level, and message
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger registry to prevent re-initialization conflicts
_loggers: dict = {}


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console_output: bool = True,
    project_root: Optional[Path] = None
) -> None:
    """
    Configure the root logger with console and optional file handlers.

    Args:
        log_level: Logging threshold (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional Path to write logs to. If None, no file handler is added.
        console_output: If True, adds a StreamHandler for console output.
        project_root: Optional base path for resolving relative log file paths.
    """
    if log_file and project_root and not log_file.is_absolute():
        log_file = project_root / log_file

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates on re-calls
    if root_logger.handlers:
        root_logger.handlers.clear()

    formatter = logging.Formatter(DEFAULT_FORMAT, datefmt=DATE_FORMAT)

    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if log_file:
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve or create a named logger.

    Args:
        name: Unique identifier for the logger (usually __name__).

    Returns:
        Configured logging.Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    # Propagate to root handlers configured in setup_logging
    logger.propagate = True
    _loggers[name] = logger
    return logger


def log_data_filtering(
    logger_name: str,
    operation: str,
    reason: str,
    count_removed: int,
    count_remaining: int,
    total_initial: Optional[int] = None
) -> None:
    """
    Log a standardized audit trail entry for data filtering operations.

    This function is critical for reproducibility, documenting exactly why
    rows were dropped during ingestion or cleaning.

    Args:
        logger_name: Name of the logger to use.
        operation: Type of operation (e.g., 'z_cut', 'quality_flag', 'coordinate_validation').
        reason: Human-readable explanation of the filter criteria.
        count_removed: Number of records removed by this filter.
        count_remaining: Number of records remaining after this filter.
        total_initial: Optional total count before this specific operation (for context).
    """
    logger = get_logger(logger_name)
    timestamp = datetime.now().isoformat()

    if total_initial is not None:
        logger.info(
            f"AUDIT: [{timestamp}] FILTER '{operation}' - "
            f"Reason: '{reason}' | "
            f"Removed: {count_removed} | "
            f"Remaining: {count_remaining} / {total_initial}"
        )
    else:
        logger.info(
            f"AUDIT: [{timestamp}] FILTER '{operation}' - "
            f"Reason: '{reason}' | "
            f"Removed: {count_removed} | "
            f"Remaining: {count_remaining}"
        )


def log_error(
    logger_name: str,
    error_type: str,
    message: str,
    context: Optional[dict] = None
) -> None:
    """
    Log a structured error event with optional context metadata.

    Args:
        logger_name: Name of the logger to use.
        error_type: Category of error (e.g., 'ValidationError', 'DataIntegrityError').
        message: Detailed error description.
        context: Optional dictionary of key-value pairs providing additional context.
    """
    logger = get_logger(logger_name)
    timestamp = datetime.now().isoformat()

    context_str = ""
    if context:
        context_str = " | Context: " + ", ".join(f"{k}={v}" for k, v in context.items())

    logger.error(
        f"ERROR: [{timestamp}] {error_type} - {message}{context_str}"
    )