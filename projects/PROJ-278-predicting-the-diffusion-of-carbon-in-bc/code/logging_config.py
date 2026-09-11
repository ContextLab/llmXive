"""Logging configuration and custom exception handlers.

This module provides:
- Custom exceptions: DataInsufficientError, PowerWarning, SHAPError
- Logger setup with deterministic formatting
- Handler functions that log and re-raise exceptions
"""
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Custom exceptions
class DataInsufficientError(Exception):
    """Raised when data is missing, insufficient, or invalid."""
    pass

class PowerWarning(Exception):
    """Raised when sample size is too low for robust statistical power."""
    pass

class SHAPError(Exception):
    """Raised when SHAP computation fails."""
    pass

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Set up a logger with console and optional file output.

    Args:
        name: Logger name (typically __name__)
        log_file: Optional path to log file. If provided, a file handler is added.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Formatter: deterministic format as per task requirements
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def handle_data_insufficient(error: DataInsufficientError):
    """Handle DataInsufficientError by logging and raising.

    Args:
        error: The DataInsufficientError instance to handle.

    Raises:
        DataInsufficientError: Re-raises the original error.
    """
    logger = logging.getLogger(__name__)
    logger.error(f"DataInsufficientError: {error}")
    raise error

def handle_power_warning(error: PowerWarning):
    """Handle PowerWarning by logging and raising.

    Args:
        error: The PowerWarning instance to handle.

    Raises:
        PowerWarning: Re-raises the original error.
    """
    logger = logging.getLogger(__name__)
    logger.warning(f"PowerWarning: {error}")
    raise error

def handle_shap_error(error: SHAPError):
    """Handle SHAPError by logging and raising.

    Args:
        error: The SHAPError instance to handle.

    Raises:
        SHAPError: Re-raises the original error.
    """
    logger = logging.getLogger(__name__)
    logger.error(f"SHAPError: {error}")
    raise error