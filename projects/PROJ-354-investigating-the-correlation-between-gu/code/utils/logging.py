"""
Logging and Error Handling Infrastructure for llmXive Gut Microbiome Study.

This module provides a centralized logging configuration and custom exception
hierarchy to ensure consistent error reporting and traceability across the
research pipeline.

Features:
- Structured logging with levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- Custom exception classes for specific domain errors (Data, Analysis, Config).
- Safe file handling for log rotation.
- Integration with project paths defined in `code/config.py`.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import traceback

# Attempt to import project config for paths; if not available, use defaults
try:
    from config import get_project_root, LOGS_DIR
except ImportError:
    # Fallback if config is not yet importable (e.g., during initial setup)
    def get_project_root() -> Path:
        return Path(__file__).parent.parent.parent

    LOGS_DIR = get_project_root() / "logs"


class LlmXiveError(Exception):
    """Base exception for all llmXive project errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()

    def __str__(self):
        base = f"{self.__class__.__name__}: {self.message}"
        if self.context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{base} [{ctx_str}]"
        return base


class DataLoadError(LlmXiveError):
    """Raised when data loading fails (network, format, missing file)."""
    pass


class PreprocessingError(LlmXiveError):
    """Raised during data preprocessing (filtering, transformation failures)."""
    pass


class AnalysisError(LlmXiveError):
    """Raised during statistical analysis (model fitting, convergence issues)."""
    pass


class ConfigError(LlmXiveError):
    """Raised when configuration is missing or invalid."""
    pass


class ValidationError(LlmXiveError):
    """Raised when data validation gates fail."""
    pass


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves or creates a logger with the project's standardized configuration.

    Args:
        name: The name of the logger (usually __name__). If None, returns the root logger.

    Returns:
        A configured logging.Logger instance.
    """
    logger_name = name if name else "llmXive.root"
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Ensure log directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # File Handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # Console Handler (for immediate feedback)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(levelname)-8s | %(name)s | %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_exception(logger: logging.Logger, exc: Exception, level: int = logging.ERROR):
    """
    Logs an exception with full traceback and context.

    Args:
        logger: The logger instance to use.
        exc: The exception to log.
        level: The logging level (default: ERROR).
    """
    exc_type = type(exc).__name__
    exc_msg = str(exc)
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    full_traceback = "".join(tb_lines)

    logger.log(
        level,
        f"Exception caught: {exc_type} - {exc_msg}",
        extra={"exc_info": True}
    )
    # Explicitly log the traceback string to ensure it's in the file even if
    # the handler configuration strips exc_info for some reason
    logger.debug(f"Traceback:\n{full_traceback}")


def safe_execute(func, *args, logger: Optional[logging.Logger] = None, **kwargs):
    """
    A utility to execute a function with robust error handling and logging.

    Args:
        func: The function to execute.
        *args: Positional arguments for func.
        logger: Logger instance (defaults to get_logger()).
        **kwargs: Keyword arguments for func.

    Returns:
        The result of func if successful.

    Raises:
        The exception raised by func, wrapped in a generic LlmXiveError if not already one.
    """
    log = logger or get_logger(func.__module__)
    log.debug(f"Executing {func.__name__}...")
    try:
        result = func(*args, **kwargs)
        log.debug(f"{func.__name__} completed successfully.")
        return result
    except LlmXiveError:
        log_exception(log, sys.exc_info()[1])
        raise
    except Exception as e:
        log_exception(log, e)
        raise AnalysisError(f"Unexpected error in {func.__name__}: {str(e)}", context={"args": args, "kwargs": kwargs})


def init_logging():
    """
    Initializes the global logging configuration for the project.
    Should be called once at the entry point of any script.
    """
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    # The get_logger function handles handler setup on first call
    get_logger()

    # Log startup info
    log = get_logger()
    log.info("Logging infrastructure initialized.")
    log.info(f"Log directory: {LOGS_DIR}")
    log.info(f"Python version: {sys.version}")


# Convenience aliases for common log levels
def debug(msg: str, logger: Optional[logging.Logger] = None):
    (logger or get_logger()).debug(msg)

def info(msg: str, logger: Optional[logging.Logger] = None):
    (logger or get_logger()).info(msg)

def warning(msg: str, logger: Optional[logging.Logger] = None):
    (logger or get_logger()).warning(msg)

def error(msg: str, logger: Optional[logging.Logger] = None):
    (logger or get_logger()).error(msg)

def critical(msg: str, logger: Optional[logging.Logger] = None):
    (logger or get_logger()).critical(msg)
