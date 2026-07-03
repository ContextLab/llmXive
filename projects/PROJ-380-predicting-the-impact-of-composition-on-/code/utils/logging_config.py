"""
Logging configuration utilities for the llmXive BMG research pipeline.

This module centralizes logging setup to ensure consistent formatting
and output across all pipeline stages.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(
    name: Optional[str] = None,
    log_level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Retrieve or create a logger with consistent configuration.

    Args:
        name: The name for the logger (e.g., 'code.data.ingest'). If None, returns root logger.
        log_level: The logging level.
        log_file: Optional path to a log file.

    Returns:
        Configured logger instance.
    """
    logger_name = name if name else "llmXive_bmg"
    logger = logging.getLogger(logger_name)

    # Return existing logger if already configured
    if logger.handlers:
        logger.setLevel(log_level)
        return logger

    logger.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def configure_root_logger(log_level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configure the root logger for the entire application.

    Args:
        log_level: The logging level.
        log_file: Optional path to a log file.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    if logger.handlers:
        return

    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)