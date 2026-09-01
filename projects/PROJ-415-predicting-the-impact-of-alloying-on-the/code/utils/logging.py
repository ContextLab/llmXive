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
    """Get a logger instance with custom formatting and file handler."""
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
    log_file = LOG_DIR / f"{name}.log"
    if LOG_DIR.exists():
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(CustomFormatter())
        logger.addHandler(fh)

    return logger

def log_error_traceback(logger: logging.Logger, e: Exception):
    """Log the exception and its traceback."""
    logger.error(f"Exception: {e}")
    logger.error(traceback.format_exc())

def log_warning(logger: logging.Logger, msg: str):
    logger.warning(msg)

def log_info(logger: logging.Logger, msg: str):
    logger.info(msg)

def log_debug(logger: logging.Logger, msg: str):
    logger.debug(msg)

def log_data_insufficiency_warning(logger: logging.Logger, msg: str):
    logger.warning(f"DATA INSUFFICIENCY: {msg}")
