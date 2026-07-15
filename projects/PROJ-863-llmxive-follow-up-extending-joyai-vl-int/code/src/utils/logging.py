"""
Logging utility for llmXive.

Provides a centralized logging configuration for the project.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with consistent formatting.

    Args:
        name: Logger name (usually __name__).
        log_file: Optional path to a log file. If provided, logs are written to file.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(file_handler)

    return logger

def setup_project_logging(log_dir: str = "logs") -> None:
    """
    Set up project-wide logging to a file in the specified directory.

    Args:
        log_dir: Directory to store log files.
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    # This function can be extended to set up multiple loggers
    pass
