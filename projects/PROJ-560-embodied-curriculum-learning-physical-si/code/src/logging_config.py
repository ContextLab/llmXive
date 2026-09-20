import logging
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_level: Optional[int] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger with console and optional file handlers.
    
    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file.
        
    Returns:
        A configured logger instance.
    """
    if log_level is None:
        log_level = logging.INFO

    logger = logging.getLogger("embodied_curriculum")
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
