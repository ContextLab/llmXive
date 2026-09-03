"""
Standardized logging and error handling utilities.

This module provides a consistent logging interface and custom exceptions
for the llmXive science pipeline.
"""

import logging
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime
import traceback

# Custom Exceptions
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataUnavailableError(PipelineError):
    """Raised when required data is missing or unavailable."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration is invalid or missing."""
    pass

class AnalysisError(PipelineError):
    """Raised when an analysis step fails."""
    pass

# Logger setup
_loggers: Dict[str, logging.Logger] = {}

def init_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Initialize the root logger and handlers.

    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If None, logs only to console.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)

    # File Handler (optional)
    if log_file:
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        root_logger.addHandler(fh)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        A configured logger instance.
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        if not logger.handlers:
            # Inherit configuration from root
            logger.setLevel(logging.DEBUG)
        _loggers[name] = logger
    return _loggers[name]

def log_progress(message: str, level: str = "INFO") -> None:
    """
    Log a progress message.

    Args:
        message: The message to log.
        level: Log level string ('INFO', 'DEBUG', 'WARNING', 'ERROR').
    """
    logger = get_logger("pipeline")
    getattr(logger, level.lower())(f"[PROGRESS] {message}")

def log_error(message: str, error: Optional[Exception] = None) -> None:
    """
    Log an error message, optionally with exception details.

    Args:
        message: The error message.
        error: Optional exception instance to include traceback.
    """
    logger = get_logger("pipeline")
    logger.error(f"[ERROR] {message}")
    if error:
        logger.error(traceback.format_exc())

def handle_fatal_error(error: Exception, exit_code: int = 1) -> None:
    """
    Handle a fatal error by logging and exiting.

    Args:
        error: The exception that caused the failure.
        exit_code: The exit code to return to the OS.
    """
    logger = get_logger("pipeline")
    logger.critical(f"FATAL ERROR: {error}")
    logger.critical(traceback.format_exc())
    sys.exit(exit_code)
