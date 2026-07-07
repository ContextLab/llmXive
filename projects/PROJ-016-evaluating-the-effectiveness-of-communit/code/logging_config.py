"""
Logging configuration for the project.
Matches the setup in T005.
"""
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
import json

PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "run.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance configured with JSON formatting (or standard if JSON lib missing).
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback if file writing fails
        logger.warning(f"Could not create file handler: {e}")

    return logger

# Initialize root logger
root_logger = get_logger()
