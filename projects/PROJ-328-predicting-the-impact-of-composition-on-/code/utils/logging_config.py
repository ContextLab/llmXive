"""
Logging configuration and utilities for the Solder Hardness Prediction Pipeline.

Provides centralized logging setup to ensure consistent formatting and log levels
across all modules.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional
from config import get_log_level, get_log_format


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger with console and optional file handlers.
    
    Args:
        log_file: Optional path to a log file. If provided, logs are written to disk.
    
    Returns:
        The configured root logger instance.
    """
    log_level = get_log_level()
    log_format = get_log_format()
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Avoid adding duplicate handlers if called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: The name of the logger (typically __name__ of the calling module).
              If None, returns the root logger.
    
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    # Ensure the logger inherits the configuration from the root
    if not logger.handlers and not logger.propagate:
        # If no handlers and not propagating, ensure it propagates to root
        logger.propagate = True
    return logger
