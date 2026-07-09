import logging
import os
import sys
from pathlib import Path
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """Custom formatter for better readability."""
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """Set up a logger with console and optional file handler."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)

    # File handler if log_file is provided
    if log_file:
        # Ensure directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(CustomFormatter())
        logger.addHandler(fh)

    return logger

def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with the specified name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Default setup if not already configured
        logger = setup_logger(name)
    return logger

if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.info("Logging module initialized successfully.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.")