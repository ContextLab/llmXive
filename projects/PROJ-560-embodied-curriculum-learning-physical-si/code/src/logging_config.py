import logging
import os
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_level: Optional[int] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger with console and optional file handlers.
    
    Args:
        log_level: Optional log level (e.g., logging.DEBUG). Defaults to INFO.
        log_file: Optional path to a log file. If None, only console output is used.
    
    Returns:
        The configured root logger.
    """
    if log_level is None:
        log_level = logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates in repeated calls
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Formatter with timestamp, level, and message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger
