"""
Base utility modules for logging and error handling.

This module provides standardized logging configuration and custom exception
classes used throughout the neural correlates analysis pipeline.
"""

import logging
import sys
import os
import traceback
from typing import Optional, Dict, Any
from pathlib import Path


# Custom Exception Classes
class PipelineError(Exception):
    """Base exception for pipeline-related errors."""
    def __init__(self, message: str, code: str = "PIPELINE_ERR"):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


class DataUnavailableError(PipelineError):
    """Raised when required data cannot be located or fetched."""
    def __init__(self, message: str):
        super().__init__(message, code="ERR_DATA_UNAVAILABLE")


class InsufficientDataError(PipelineError):
    """Raised when data volume is below required thresholds (e.g., subject count)."""
    def __init__(self, message: str):
        super().__init__(message, code="ERR_N_INSUFFICIENT")


class ConfigError(PipelineError):
    """Raised when configuration files are missing or invalid."""
    def __init__(self, message: str):
        super().__init__(message, code="ERR_CONFIG")


class IntegrityError(PipelineError):
    """Raised when data integrity checks (hashes) fail."""
    def __init__(self, message: str):
        super().__init__(message, code="ERR_INTEGRITY")


# Logging Configuration
_logger_instance: Optional[logging.Logger] = None
_logging_setup = False


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None,
    project_root: Optional[Path] = None
) -> None:
    """
    Configure the root logger for the pipeline.

    Args:
        log_level: Logging severity threshold (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If None, logs to stderr only.
        project_root: Optional base path for relative log file resolution.
    """
    global _logging_setup

    if _logging_setup:
        return

    # Define log format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates in repeated runs
    root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler (if specified)
    if log_file:
        # Resolve path relative to project_root if provided
        if project_root and not log_file.is_absolute():
            log_file = project_root / log_file
        
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_formatter)
        root_logger.addHandler(file_handler)

    _logging_setup = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger instance, initializing logging if necessary.

    Args:
        name: Name for the logger (e.g., module name). Defaults to 'pipeline'.

    Returns:
        Configured logger instance.
    """
    global _logger_instance

    if not _logging_setup:
        # Default setup if get_logger is called before explicit setup_logging
        setup_logging()

    logger_name = name if name else "pipeline"
    return logging.getLogger(logger_name)


def log_exception(
    logger: logging.Logger,
    exc: Exception,
    msg: str = "An unexpected error occurred",
    level: int = logging.ERROR
) -> None:
    """
    Log an exception with full traceback information.

    Args:
        logger: Logger instance to use.
        exc: The exception object.
        msg: Preceding message to log.
        level: Log level for the error (default: ERROR).
    """
    exc_type = type(exc).__name__
    exc_traceback = traceback.format_exc()
    
    error_detail = f"{msg}: {exc_type} - {str(exc)}"
    
    if logger.isEnabledFor(level):
        logger.log(level, error_detail)
        logger.log(level, "Traceback:\n%s", exc_traceback)