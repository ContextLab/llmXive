"""
Standardized logging configuration for the MgB2 Impurity Impact project.

Provides specialized loggers for ingestion, modeling, and visualization modules
with consistent formatting and output handlers.
"""
import logging
import sys
from pathlib import Path
from typing import Optional


# Default log level
DEFAULT_LEVEL = logging.INFO

# Log format structure
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Cache for loggers to ensure single instance per name
_logger_cache: dict = {}


def _get_formatter() -> logging.Formatter:
    """Create and return the standard log formatter."""
    return logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)


def _create_handler(stream: sys.stdout = sys.stderr) -> logging.StreamHandler:
    """Create a standard stream handler with the project formatter."""
    handler = logging.StreamHandler(stream)
    handler.setFormatter(_get_formatter())
    return handler


def get_logger(
    name: str,
    level: int = DEFAULT_LEVEL,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Get or create a logger with the specified name.

    Args:
        name: The name of the logger (usually __name__ or module path).
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to write logs to a file.

    Returns:
        A configured logging.Logger instance.
    """
    if name in _logger_cache:
        return _logger_cache[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        # Add console handler
        console_handler = _create_handler()
        logger.addHandler(console_handler)

        # Add file handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(_get_formatter())
            logger.addHandler(file_handler)

    # Prevent propagation to root logger to avoid duplicate console output
    logger.propagate = False

    _logger_cache[name] = logger
    return logger


def get_ingestion_logger() -> logging.Logger:
    """
    Get the logger specifically for data ingestion tasks.

    Returns:
        A logger named 'ingestion' with INFO level.
    """
    return get_logger("ingestion", level=DEFAULT_LEVEL)


def get_modeling_logger() -> logging.Logger:
    """
    Get the logger specifically for model training and evaluation tasks.

    Returns:
        A logger named 'modeling' with INFO level.
    """
    return get_logger("modeling", level=DEFAULT_LEVEL)


def get_visualization_logger() -> logging.Logger:
    """
    Get the logger specifically for visualization and plotting tasks.

    Returns:
        A logger named 'visualization' with INFO level.
    """
    return get_logger("visualization", level=DEFAULT_LEVEL)


# Convenience function for testing or quick access
def get_project_logger() -> logging.Logger:
    """
    Get the main project logger.

    Returns:
        A logger named 'mgb2_project' with INFO level.
    """
    return get_logger("mgb2_project", level=DEFAULT_LEVEL)
