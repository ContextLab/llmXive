"""
Logging configuration module.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        log_file: Optional path to a log file. If None, logs to stdout only.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers = []

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler (if specified)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__).

    Returns:
        logging.Logger: Configured logger.
    """
    return logging.getLogger(name)
