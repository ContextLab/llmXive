"""
Logging utilities for social memory networks experiments.

This module provides centralized logging configuration with timestamps
for all experiment-related logging. Logs are written to experiment.log
in the project root or a configurable output directory.

FR-010: Configure error logging with timestamps to experiment.log
"""

import logging
import os
from pathlib import Path
from typing import Optional, Union
from datetime import datetime

# Default log file path
DEFAULT_LOG_FILE = "experiment.log"

# Log format with timestamp
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str = "social_memory",
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
    output_dir: Optional[Union[str, Path]] = None,
) -> logging.Logger:
    """
    Set up and return a configured logger for the experiment.

    Args:
        name: Logger name (default: "social_memory")
        log_file: Log file name (default: "experiment.log")
        level: Logging level (default: logging.INFO)
        output_dir: Directory for log file (default: current working directory)

    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Determine log file path
    if log_file is None:
        log_file = DEFAULT_LOG_FILE
    if output_dir is None:
        output_dir = Path.cwd()

    log_path = Path(output_dir) / log_file

    # Create output directory if it doesn't exist
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create file handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(level)

    # Create formatter with timestamp
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

    # Also add console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "social_memory") -> logging.Logger:
    """
    Get an existing logger or create a new one with default configuration.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        return setup_logger(name=name)

    return logger


def log_experiment_start(
    experiment_name: str,
    config: Optional[dict] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log the start of an experiment with metadata.

    Args:
        experiment_name: Name of the experiment
        config: Optional configuration dictionary to log
        logger: Logger instance (uses default if not provided)
    """
    if logger is None:
        logger = get_logger()

    timestamp = datetime.now().strftime(DATE_FORMAT)
    logger.info(f"=== EXPERIMENT START: {experiment_name} at {timestamp} ===")

    if config:
        logger.info("Configuration:")
        for key, value in config.items():
            logger.info(f"  {key}: {value}")


def log_experiment_end(
    experiment_name: str,
    success: bool = True,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log the end of an experiment.

    Args:
        experiment_name: Name of the experiment
        success: Whether the experiment completed successfully
        logger: Logger instance (uses default if not provided)
    """
    if logger is None:
        logger = get_logger()

    status = "SUCCESS" if success else "FAILED"
    logger.info(f"=== EXPERIMENT END: {experiment_name} - {status} ===")


# Convenience functions for common logging operations
def info(msg: str, logger: Optional[logging.Logger] = None) -> None:
    """Log an info message."""
    if logger is None:
        logger = get_logger()
    logger.info(msg)


def warning(msg: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a warning message."""
    if logger is None:
        logger = get_logger()
    logger.warning(msg)


def error(msg: str, logger: Optional[logging.Logger] = None) -> None:
    """Log an error message."""
    if logger is None:
        logger = get_logger()
    logger.error(msg)


def debug(msg: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a debug message."""
    if logger is None:
        logger = get_logger()
    logger.debug(msg)


def critical(msg: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a critical message."""
    if logger is None:
        logger = get_logger()
    logger.critical(msg)
