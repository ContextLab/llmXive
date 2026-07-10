"""
llmXive Project: Predicting Plant Drought Tolerance from RSA Data
Logging Infrastructure Initialization
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import os

# Project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "state" / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configuration constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3
DEFAULT_LEVEL = logging.INFO

# Global logger instance
_logger = None


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a configured logger instance for the project.
    
    Args:
        name: Name of the logger (e.g., 'llmXive', 'code.download_images')
    
    Returns:
        A configured logging.Logger instance.
    """
    global _logger
    
    # Initialize the root logger if not already done
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(DEFAULT_LEVEL)
        
        # Prevent adding handlers multiple times if called repeatedly
        if not _logger.handlers:
            # Console Handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(DEFAULT_LEVEL)
            console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            _logger.addHandler(console_handler)
            
            # File Handler (Rotating)
            try:
                file_handler = RotatingFileHandler(
                    LOG_FILE,
                    maxBytes=MAX_BYTES,
                    backupCount=BACKUP_COUNT,
                    encoding="utf-8"
                )
                file_handler.setLevel(DEFAULT_LEVEL)
                file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
                _logger.addHandler(file_handler)
            except Exception as e:
                # Fallback if file logging fails (e.g., permissions)
                console_handler.error(f"Failed to initialize file logging: {e}")
    
    # Return a child logger for the specific module if name differs
    if name != "llmXive":
        return logging.getLogger(name)
    
    return _logger


def setup_logging(level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Explicitly initializes the logging infrastructure with a specific level.
    This is useful if the user wants to change verbosity before any other imports.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.WARNING)
    
    Returns:
        The root project logger.
    """
    global _logger
    _logger = None  # Reset to force re-initialization with new level
    
    # Set level on the root module logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates if called multiple times
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Re-initialize the project logger
    return get_logger("llmXive")


# Initialize default logger on module import
get_logger()