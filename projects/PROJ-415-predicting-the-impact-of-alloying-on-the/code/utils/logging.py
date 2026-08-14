"""
Standardized logging and error tracking utilities.
"""

import logging
import os
from pathlib import Path
from typing import Optional
import traceback

from config import LOG_DIR, PROJECT_ROOT

class CustomFormatter(logging.Formatter):
    """Custom formatter for logging."""
    def format(self, record):
        log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self._style._fmt = log_fmt
        return super().format(record)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance configured for the project.
    
    Args:
        name: The name of the logger (usually __name__)
        
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    
    # Create file handler
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{name}.log"
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(CustomFormatter())
    logger.addHandler(fh)
    
    return logger

def log_error_traceback(logger: logging.Logger, message: str) -> None:
    """
    Log an error message along with the traceback.
    
    Args:
        logger: The logger instance to use.
        message: The error message.
    """
    error_msg = f"{message}\n{traceback.format_exc()}"
    logger.error(error_msg)

def log_warning(logger: logging.Logger, message: str) -> None:
    """
    Log a warning message.
    
    Args:
        logger: The logger instance to use.
        message: The warning message.
    """
    logger.warning(message)

def log_info(logger: logging.Logger, message: str) -> None:
    """
    Log an info message.
    
    Args:
        logger: The logger instance to use.
        message: The info message.
    """
    logger.info(message)

def log_debug(logger: logging.Logger, message: str) -> None:
    """
    Log a debug message.
    
    Args:
        logger: The logger instance to use.
        message: The debug message.
    """
    logger.debug(message)

def log_data_insufficiency_warning(logger: logging.Logger, n: int) -> None:
    """
    Log a warning about data insufficiency.
    
    Args:
        logger: The logger instance to use.
        n: The number of data points.
    """
    logger.warning(f"Data Insufficiency: N < 50 (N={n})")
