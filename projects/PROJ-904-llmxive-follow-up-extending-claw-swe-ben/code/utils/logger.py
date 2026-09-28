"""
Logging and error handling infrastructure for the llmXive project.

This module provides centralized logging configuration and custom exception classes
to ensure consistent error handling across the research pipeline.
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional
from datetime import datetime

# Custom Exception Hierarchy
class ResearchError(Exception):
    """Base class for all research-related errors."""
    pass


class DataLoadError(ResearchError):
    """Raised when data loading fails."""
    pass


class ModelExecutionError(ResearchError):
    """Raised when model execution fails."""
    pass


class ConfigurationError(ResearchError):
    """Raised when configuration is invalid."""
    pass


class AnalysisError(ResearchError):
    """Raised when analysis fails."""
    pass


def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with console and optional file output.

    Args:
        name: Logger name.
        log_file: Optional path to log file.
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def log_error(error: Exception, context: Optional[str] = None) -> str:
    """
    Log an error with full traceback and context.

    Args:
        error: The exception to log.
        context: Optional context description.

    Returns:
        The error message.
    """
    logger = logging.getLogger(__name__)
    error_type = type(error).__name__
    error_msg = str(error)
    timestamp = datetime.now().isoformat()

    log_entry = {
        "timestamp": timestamp,
        "error_type": error_type,
        "message": error_msg,
        "context": context,
        "traceback": traceback.format_exc()
    }

    logger.error(f"[{error_type}] {error_msg} | Context: {context or 'None'}")
    logger.debug(f"Traceback:\n{log_entry['traceback']}")

    return error_msg


def safe_execute(func, *args, **kwargs):
    """
    Execute a function with safe error handling.

    Args:
        func: Function to execute.
        *args: Positional arguments.
        **kwargs: Keyword arguments.

    Returns:
        Tuple of (success: bool, result: Any, error: Optional[Exception])
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        log_error(e, context=f"Function: {func.__name__}")
        return False, None, e