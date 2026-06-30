"""
Standardized logging configuration for the llmXive MgB2 Impurity Impact project.

Provides pre-configured loggers for ingestion, modeling, and visualization modules.
Ensures consistent log formatting, levels, and output destinations across the pipeline.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Project root relative to this file (code/src/utils/logging.py -> code/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "logs"

# Default log format including timestamp, level, module, and message
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Ensure log directory exists
_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _get_file_handler(module_name: str) -> logging.FileHandler:
    """
    Create a file handler for a specific module logger.

    Args:
        module_name: The name of the module (e.g., 'ingestion', 'modeling').

    Returns:
        A configured FileHandler writing to a log file in the logs/ directory.
    """
    log_file = _LOG_DIR / f"{module_name}.log"
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    return handler


def _get_console_handler() -> logging.StreamHandler:
    """
    Create a console handler with standard formatting.

    Returns:
        A configured StreamHandler writing to stdout.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    return handler


def get_logger(name: str, level: int = logging.INFO, to_file: bool = True) -> logging.Logger:
    """
    Retrieve or create a logger with standardized configuration.

    Args:
        name: The name of the logger (typically __name__ of the calling module).
        level: The logging level (default: INFO).
        to_file: If True, also writes logs to a file in the logs/ directory.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # Add console handler
    console_handler = _get_console_handler()
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # Add file handler if requested
    if to_file:
        # Use the last part of the logger name for the log file (e.g., 'ingestion' from 'src.ingestion.download')
        file_module_name = name.split(".")[-1]
        file_handler = _get_file_handler(file_module_name)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger


# Pre-configured loggers for the three main domains
# These are convenience accessors to ensure consistent naming and configuration

def get_ingestion_logger(level: int = logging.INFO) -> logging.Logger:
    """
    Get the standardized logger for data ingestion tasks.

    Args:
        level: The logging level.

    Returns:
        A logger configured for ingestion operations.
    """
    return get_logger("ingestion", level=level, to_file=True)


def get_modeling_logger(level: int = logging.INFO) -> logging.Logger:
    """
    Get the standardized logger for model training and evaluation tasks.

    Args:
        level: The logging level.

    Returns:
        A logger configured for modeling operations.
    """
    return get_logger("modeling", level=level, to_file=True)


def get_visualization_logger(level: int = logging.INFO) -> logging.Logger:
    """
    Get the standardized logger for visualization and plotting tasks.

    Args:
        level: The logging level.

    Returns:
        A logger configured for visualization operations.
    """
    return get_logger("visualization", level=level, to_file=True)


# Module-level convenience for immediate use in scripts
# Example: from code.src.utils.logging import logger
logger = get_logger("utils.logging")
