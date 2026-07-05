"""
Logging module for error handling and filtered logs.

This module provides centralized logging configuration for the project,
including log levels, formatting, and file output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from src.utils.config import get_project_root, get_interim_data_dir

# Log file path
_LOG_FILE = get_interim_data_dir() / 'pipeline.log'

# Log format
_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Default log level
_DEFAULT_LEVEL = logging.INFO

def setup_logger(
    name: str,
    level: int = _DEFAULT_LEVEL,
    log_to_file: bool = True
) -> logging.Logger:
    """
    Set up a logger with console and optional file output.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (default: INFO)
        log_to_file: Whether to log to file (default: True)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(_LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if log_to_file:
        _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(_LOG_FILE)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_log_file() -> Path:
    """
    Get the path to the log file.
    
    Returns:
        Path to the log file
    """
    return _LOG_FILE

def clear_logs():
    """
    Clear the log file if it exists.
    """
    if _LOG_FILE.exists():
        _LOG_FILE.unlink()
        logging.getLogger().info("Log file cleared")

# Initialize root logger
root_logger = setup_logger('root')
