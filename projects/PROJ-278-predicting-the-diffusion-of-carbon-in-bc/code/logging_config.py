"""Logging configuration and error handling infrastructure."""
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from .exceptions import DataInsufficientError, PowerWarning, SHAPError

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger with console and optional file output."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def handle_data_insufficient(error: DataInsufficientError):
    """Handle DataInsufficientError by logging and re-raising."""
    logging.error(f"Data Insufficient Error: {error}")
    raise error

def handle_power_warning(warning: PowerWarning):
    """Handle PowerWarning by logging."""
    logging.warning(f"Power Warning: {warning}")

def handle_shap_error(error: SHAPError):
    """Handle SHAPError by logging and halting."""
    logging.error(f"SHAP Error: {error}")
    raise error
