"""
Deterministic logging and error handling infrastructure.

Provides:
- setup_logger(): Configures a deterministic logger with file and console handlers.
- log_error(): Centralized error logging with stack trace capture.
- safe_execute(): Utility to execute functions with error handling.
- Custom Exception hierarchy for research-specific errors.
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional
from datetime import datetime

# Ensure deterministic logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ResearchError(Exception):
    """Base class for all research-specific errors."""
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()

    def __str__(self):
        if self.context:
            return f"{self.message} (Context: {self.context})"
        return self.message


class DataLoadError(ResearchError):
    """Raised when data loading fails."""
    pass


class ModelExecutionError(ResearchError):
    """Raised when model execution fails."""
    pass


class ConfigurationError(ResearchError):
    """Raised when configuration is invalid or missing."""
    pass


class AnalysisError(ResearchError):
    """Raised when analysis fails."""
    pass


def setup_logger(
    name: str = "llmXive",
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Configure and return a logger with deterministic formatting.

    Args:
        name: Logger name (default: "llmXive")
        log_file: Optional path to write logs to. If None, only console output.
        level: Logging level (default: INFO)
        console: Whether to log to console (default: True)

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_file:
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[dict] = None,
    level: int = logging.ERROR
) -> None:
    """
    Log an error with full stack trace and optional context.

    Args:
        logger: Logger instance to use.
        error: The exception to log.
        context: Optional dictionary of context information.
        level: Logging level for the error (default: ERROR).
    """
    error_type = type(error).__name__
    error_message = str(error)
    stack_trace = traceback.format_exc()

    log_msg = f"{error_type}: {error_message}"
    if context:
        log_msg += f" | Context: {context}"

    logger.log(level, log_msg)
    logger.debug(f"Stack trace:\n{stack_trace}")


def safe_execute(
    func,
    logger: Optional[logging.Logger] = None,
    default_return: Optional[any] = None,
    raise_on_error: bool = True
):
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute.
        logger: Optional logger for error reporting.
        default_return: Value to return on error if raise_on_error is False.
        raise_on_error: If True, re-raise the exception after logging.

    Returns:
        Function result or default_return on error.

    Raises:
        The original exception if raise_on_error is True.
    """
    try:
        return func()
    except Exception as e:
        if logger:
            log_error(logger, e)
        if raise_on_error:
            raise
        return default_return
