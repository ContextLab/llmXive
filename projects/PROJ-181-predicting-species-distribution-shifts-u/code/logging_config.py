import logging
import os
import sys
from pathlib import Path
from config import LOGS_DIR

# Ensure the logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Define a custom formatter to include timestamp, level, and module
class DetailedFormatter(logging.Formatter):
    def format(self, record):
        # Add relative path info if available
        if hasattr(record, 'relative_path'):
            record.msg = f"[{record.relative_path}] {record.msg}"
        return super().format(record)

def setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure a logger that writes to a specific file in the logs directory.

    Args:
        name (str): The name of the logger.
        log_file (str): The filename (relative to logs/ directory) for the log output.
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if the logger is called multiple times
    if logger.handlers:
        return logger

    # Create file handler for the specific log file
    log_path = Path(LOGS_DIR) / log_file
    file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
    file_handler.setLevel(level)

    # Create console handler for general visibility
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Create formatter
    formatter = DetailedFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def get_logger(name: str = 'project') -> logging.Logger:
    """
    Retrieve a logger instance. If it doesn't exist, it will be created with default settings.
    This is a convenience wrapper to ensure consistent logger retrieval.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The logger instance.
    """
    return logging.getLogger(name)