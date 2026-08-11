import logging
import sys
import os
from pathlib import Path
from typing import Optional
from config import get_log_level, get_log_format

_logger_instance: Optional[logging.Logger] = None

def setup_logging() -> None:
    """
    Configures the root logger for the application.
    """
    log_level = get_log_level()
    log_format = get_log_format()
    
    # Create a formatter
    formatter = logging.Formatter(log_format)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates if called multiple times
    root_logger.handlers = []
    root_logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves or creates a logger with the specified name.
    Ensures logging is set up first.
    """
    global _logger_instance
    if not _logger_instance:
        setup_logging()
        _logger_instance = logging.getLogger()
    
    logger = logging.getLogger(name)
    # Ensure the logger inherits the level and handlers from root if not explicitly set
    if not logger.handlers and not logger.level:
        logger.setLevel(get_log_level())
    return logger
