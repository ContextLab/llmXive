"""
Logging infrastructure for the llmXive automated science pipeline.

Provides timestamped, multi-level logging with error code tracking.
Integrates with loguru and ensures consistent formatting across the project.
"""
import os
import sys
import logging
from pathlib import Path
from loguru import logger
from datetime import datetime
import traceback

# Global state for error code tracking
_error_codes = set()
_log_file_path = None

def setup_logger(
    log_file: str = "data/pipeline.log",
    level: str = "INFO",
    error_code: str | None = None
) -> None:
    """
    Configure the global logger instance.

    Args:
        log_file: Path to the log file (relative to project root).
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        error_code: Optional error code to associate with the current run context.
    """
    global _log_file_path

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _log_file_path = str(log_path.absolute())

    # Remove default handlers
    logger.remove()

    # Parse level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Add console handler with formatted output
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # Add file handler with timestamped output
    logger.add(
        str(log_path),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=log_level,
        rotation="10 MB",
        retention="1 month",
        compression="gz"
    )

    logger.info(f"Logger initialized. Output: {log_path}")

    if error_code:
        track_error(error_code)
        logger.info(f"Error code tracked: {error_code}")

def track_error(error_code: str) -> None:
    """
    Track an error code for audit purposes.

    Args:
        error_code: Unique identifier for the error type.
    """
    _error_codes.add(error_code)
    logger.error(f"[ERROR-CODE: {error_code}] An error occurred.")

def get_tracked_errors() -> set:
    """Return the set of tracked error codes."""
    return _error_codes.copy()

def log_error(message: str, error_code: str | None = None) -> None:
    """
    Log an error message with optional error code tracking.

    Args:
        message: Error message to log.
        error_code: Optional error code to track.
    """
    if error_code:
        track_error(error_code)
    logger.error(message)

def log_critical(message: str, error_code: str | None = None) -> None:
    """
    Log a critical error message with optional error code tracking.

    Args:
        message: Critical error message to log.
        error_code: Optional error code to track.
    """
    if error_code:
        track_error(error_code)
    logger.critical(message)

def log_exception(message: str, exc_info: Exception | None = None, error_code: str | None = None) -> None:
    """
    Log an exception with traceback.

    Args:
        message: Error message to log.
        exc_info: Exception instance (optional, if None, current exception is used).
        error_code: Optional error code to track.
    """
    if error_code:
        track_error(error_code)
    
    if exc_info:
        logger.opt(exception=exc_info).error(f"{message}: {exc_info}")
    else:
        logger.opt(exception=True).error(message)

# Initialize with default settings if not explicitly called
# This allows modules to import and use logger immediately
if not _log_file_path:
    setup_logger()