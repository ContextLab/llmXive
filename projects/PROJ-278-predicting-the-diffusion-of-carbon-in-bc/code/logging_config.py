"""
Deterministic logging and error handling infrastructure.

This module provides:
1. A standardized logger setup with deterministic formatting.
2. Handlers for custom exceptions (DataInsufficientError, PowerWarning, SHAPError).
3. Integration with the project's configuration for log levels and output paths.
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from .exceptions import DataInsufficientError, PowerWarning, SHAPError


# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logger(
    name: str = "diffusion_pipeline",
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    deterministic: bool = True
) -> logging.Logger:
    """
    Configure and return a project-wide logger.

    Args:
        name: The name of the logger.
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If None, logs only to stderr.
        deterministic: If True, removes timestamps from console output to ensure
                       identical logs for identical runs (useful for CI diffs).
                       Note: File logs always include timestamps for audit trails.

    Returns:
        A configured logging.Logger instance.
    """
    global _logger

    if _logger is not None and _logger.name == name:
        return _logger

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates in re-runs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter for file logs (includes timestamp)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Formatter for console logs (deterministic if requested)
    if deterministic:
        console_formatter = logging.Formatter(
            "%(levelname)s - %(message)s"
        )
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler (if path provided)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, mode='a')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    _logger = logger
    return logger


def handle_data_insufficient(error: DataInsufficientError, logger: Optional[logging.Logger] = None) -> None:
    """
    Handler for DataInsufficientError.
    Logs the error at ERROR level and re-raises it to halt execution.

    Args:
        error: The caught exception.
        logger: Optional logger instance.
    """
    log = logger or logging.getLogger("diffusion_pipeline")
    log.error(f"CRITICAL: {error}")
    log.error("Aborting pipeline due to insufficient data.")
    raise error


def handle_power_warning(error: PowerWarning, logger: Optional[logging.Logger] = None) -> None:
    """
    Handler for PowerWarning.
    Logs the warning at WARNING level.
    Execution continues (typically triggering LOOCV fallback in the caller).

    Args:
        error: The caught exception.
        logger: Optional logger instance.
    """
    log = logger or logging.getLogger("diffusion_pipeline")
    log.warning(f"POWER WARNING: {error}")
    # Do not re-raise; execution continues with fallback logic


def handle_shap_error(error: SHAPError, logger: Optional[logging.Logger] = None) -> None:
    """
    Handler for SHAPError.
    Logs the error at ERROR level and re-raises it to halt execution.
    No fallback is permitted for SHAP failures.

    Args:
        error: The caught exception.
        logger: Optional logger instance.
    """
    log = logger or logging.getLogger("diffusion_pipeline")
    log.error(f"SHAP FAILURE: {error}")
    log.error("Aborting pipeline. Feature importance analysis is critical and cannot be approximated.")
    raise error
