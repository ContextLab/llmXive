"""
Standardized logging configuration for the MgB2 Impurity Impact pipeline.

Provides pre-configured loggers for ingestion, modeling, and visualization
stages, ensuring consistent formatting, levels, and output destinations.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Base configuration to ensure consistent formatting across all loggers
_BASE_FORMATTER = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Cache for created loggers to prevent re-configuration
_LOGGERS: dict[str, logging.Logger] = {}


def _get_console_handler() -> logging.StreamHandler:
    """Create a console handler with standard formatting."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_BASE_FORMATTER)
    handler.setLevel(logging.INFO)
    return handler


def _get_file_handler(log_file: Path) -> logging.FileHandler:
    """Create a file handler for a specific log file."""
    # Ensure the directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_file)
    handler.setFormatter(_BASE_FORMATTER)
    handler.setLevel(logging.DEBUG)
    return handler


def get_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Retrieve or create a named logger with standard configuration.

    Args:
        name: The name of the logger (e.g., 'mgb2.ingestion').
        level: The logging level (default: INFO).
        log_file: Optional path to a log file. If provided, logs are also
                  written to disk.

    Returns:
        A configured logging.Logger instance.
    """
    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Prevent duplicate logs from root handlers

    # Add console handler
    console_handler = _get_console_handler()
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # Add file handler if requested
    if log_file:
        file_handler = _get_file_handler(log_file)
        file_handler.setLevel(logging.DEBUG)  # File gets all debug info
        logger.addHandler(file_handler)

    _LOGGERS[name] = logger
    return logger


def get_ingestion_logger(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Get the standardized logger for the data ingestion stage.

    Args:
        log_file: Optional path to write ingestion logs.

    Returns:
        Configured logger for ingestion tasks.
    """
    return get_logger(
        name="mgb2.ingestion",
        level=logging.INFO,
        log_file=log_file
    )


def get_modeling_logger(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Get the standardized logger for the model training stage.

    Args:
        log_file: Optional path to write modeling logs.

    Returns:
        Configured logger for modeling tasks.
    """
    return get_logger(
        name="mgb2.modeling",
        level=logging.INFO,
        log_file=log_file
    )


def get_visualization_logger(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Get the standardized logger for the visualization stage.

    Args:
        log_file: Optional path to write visualization logs.

    Returns:
        Configured logger for visualization tasks.
    """
    return get_logger(
        name="mgb2.visualization",
        level=logging.INFO,
        log_file=log_file
    )