"""
Logging infrastructure for the pipeline.
"""
import logging
import os
from pathlib import Path

from config import LOG_LEVEL, LOG_FORMAT, LOGS_DIR

def setup_logging():
    """Configure global logging."""
    log_file = LOGS_DIR / "pipeline.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Clear existing handlers
    logger.handlers = []

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(LOG_FORMAT)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)

# Initialize logging on module import
setup_logging()
