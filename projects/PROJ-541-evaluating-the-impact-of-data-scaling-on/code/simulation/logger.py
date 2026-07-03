"""
Logging configuration for the simulation module.

Provides a centralized setup function to configure logger instances
with consistent formatting and log levels, including file rotation.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: str = "logs/simulation.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup and return a logger instance configured with specific format, level,
    and file rotation.

    This function creates a logger with the given name, sets its level to handle
    DEBUG, INFO, WARNING, and ERROR, and attaches both a console handler and a
    rotating file handler.

    Args:
        name: The name of the logger (typically __name__ of the calling module).
        level: The logging level (default: logging.INFO).
        log_file: Path to the log file (default: "logs/simulation.log").
        max_bytes: Maximum size of log file before rotation (default: 10MB).
        backup_count: Number of backup log files to keep (default: 5).

    Returns:
        A configured logging.Logger instance.

    The format string used is:
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    """
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Only add handlers if none exist to prevent duplicate logs in tests/re-runs
    if not logger.handlers:
        # Define the specific format string required by the task
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Prevent propagation to root logger to avoid double logging
        logger.propagate = False

    return logger