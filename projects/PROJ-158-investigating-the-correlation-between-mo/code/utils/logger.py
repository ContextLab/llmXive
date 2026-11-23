"""
Logger setup for the project.
"""
import logging
import os
from pathlib import Path
from utils.config import LOGS_DIR

def setup_logger(name: str = "dssc_project") -> logging.Logger:
    """
    Sets up a logger that writes to code/logs/app.log and stdout.
    """
    # Ensure log directory exists
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True)

    log_file = LOGS_DIR / "app.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
