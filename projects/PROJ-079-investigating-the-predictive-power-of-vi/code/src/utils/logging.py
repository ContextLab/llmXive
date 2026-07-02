"""
Logging configuration for the llmXive research pipeline.
Provides a configured logger and file setup utilities.
"""
import logging
import sys
from pathlib import Path
from src.config import ARTIFACTS_PATH

# Ensure the artifacts path exists for log files
LOGS_DIR = Path(ARTIFACTS_PATH) / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

_logger = None


def setup_log_file(filename: str = "pipeline.log") -> Path:
    """
    Ensure the log file path exists and returns the Path object.
    Creates the directory structure if it doesn't exist.
    """
    log_path = LOGS_DIR / filename
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a configured logger instance.
    If a logger with this name already exists, returns it.
    Otherwise, creates a new one with console and file handlers.
    """
    global _logger
    
    # Check if logger already exists in the hierarchy
    existing_logger = logging.getLogger(name)
    if existing_logger.hasHandlers():
        return existing_logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Clear any existing handlers to avoid duplicates in some environments
    logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File Handler
    log_file = setup_log_file("pipeline.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger
