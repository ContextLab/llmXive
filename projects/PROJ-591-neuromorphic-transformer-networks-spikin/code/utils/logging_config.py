"""
Centralized logging configuration for the Neuromorphic Transformer project.

This module provides a consistent logging setup to be imported by all
major components (main.py, metrics, analysis) to ensure uniform log
formatting and output destinations.
"""

import logging
import sys
import os

# Default log level
DEFAULT_LEVEL = logging.INFO

# Log format string
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging(
    name: str = "neuromorphic_transformer",
    level: int = DEFAULT_LEVEL,
    log_file: str = None
) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.

    Args:
        name: The name of the logger (usually __name__ of the caller).
        level: The logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If None, logs only to stdout.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Clear any existing handlers to ensure clean state
    logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler (optional)
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: str = "neuromorphic_transformer") -> logging.Logger:
    """
    Retrieve an existing logger or create a new one with default settings.

    Args:
        name: The name of the logger.

    Returns:
        A logging.Logger instance.
    """
    return logging.getLogger(name)
