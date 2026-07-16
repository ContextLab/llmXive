"""
Base logging and error handling utilities for the project.

Provides a centralized logger configuration and custom exception classes
to ensure consistent error reporting and debugging across the pipeline.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Union


class PipelineError(Exception):
    """Base exception for all pipeline-related errors."""
    pass


class DataFetchError(PipelineError):
    """Raised when fetching external data fails."""
    pass


class ConfigurationError(PipelineError):
    """Raised when configuration loading or validation fails."""
    pass


class ProcessingError(PipelineError):
    """Raised during data processing steps (e.g., parcellation, centrality)."""
    pass


class ValidationFailedError(PipelineError):
    """Raised when data validation checks fail."""
    pass


def get_logger(
    name: Optional[str] = None,
    log_level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    include_timestamp: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        name: Logger name. If None, uses 'llmXive.pipeline'.
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to write logs to. If None, logs only to stderr.
        include_timestamp: Whether to include timestamps in log format.

    Returns:
        Configured logging.Logger instance.

    Example:
        >>> logger = get_logger("my_module", log_file="logs/pipeline.log")
        >>> logger.info("Processing started")
    """
    logger_name = name or "llmXive.pipeline"
    logger = logging.getLogger(logger_name)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        logger.setLevel(log_level)
        return logger

    logger.setLevel(log_level)
    logger.propagate = False  # Prevent duplicate logs from root logger

    # Define format string
    if include_timestamp:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    else:
        log_format = "%(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    return logger


def log_error_and_raise(
    logger: logging.Logger,
    error: Exception,
    message: Optional[str] = None,
    error_type: type = PipelineError,
) -> None:
    """
    Log an error message and raise a new exception.

    Args:
        logger: The logger instance to use.
        error: The original exception causing this error.
        message: Optional custom message to log.
        error_type: The type of exception to raise (default: PipelineError).

    Raises:
        error_type: A new exception wrapping the original error.
    """
    full_message = message or f"Error occurred: {str(error)}"
    logger.error(f"{full_message} | Original error: {type(error).__name__}: {error}", exc_info=True)
    raise error_type(full_message) from error