"""
Utility functions for PROJ-200.

This module provides common logging and configuration utilities.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

from .config import get_project_root

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Sets up the logging configuration for the project.

    Args:
        log_level (int): The logging level (e.g., logging.INFO).
        log_file (Optional[str]): Path to a log file. If None, logs to console only.

    Returns:
        logging.Logger: The root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Gets a logger with a specific name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The logger instance.
    """
    return logging.getLogger(name)
