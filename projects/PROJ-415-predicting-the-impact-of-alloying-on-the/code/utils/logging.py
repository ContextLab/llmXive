import logging
import os
from pathlib import Path
from typing import Optional
import traceback
from config import LOG_DIR, PROJECT_ROOT

class CustomFormatter(logging.Formatter):
    """Custom formatter for better readability."""
    def format(self, record):
        log_fmt = f"%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance configured to write to console and file.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)

    # File handler
    log_file = LOG_DIR / "pipeline.log"
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(CustomFormatter())
    logger.addHandler(fh)

    return logger

def log_error_traceback(logger: logging.Logger, error: Exception) -> None:
    """Log the full traceback of an exception."""
    logger.error(f"Exception occurred: {str(error)}")
    logger.error(traceback.format_exc())

def log_warning(logger: logging.Logger, message: str) -> None:
    """Log a warning message."""
    logger.warning(message)

def log_info(logger: logging.Logger, message: str) -> None:
    """Log an info message."""
    logger.info(message)

def log_debug(logger: logging.Logger, message: str) -> None:
    """Log a debug message."""
    logger.debug(message)

def log_data_insufficiency_warning(logger: logging.Logger, count: int) -> None:
    """Log a specific warning for data insufficiency."""
    logger.warning(f"Data Insufficiency: N < 50 (Current count: {count})")
