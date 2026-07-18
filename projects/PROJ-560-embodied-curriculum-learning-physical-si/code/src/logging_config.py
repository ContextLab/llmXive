import logging
import os
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_level: Optional[int] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure and return the root logger for the project.
    
    Sets up handlers for both console (stdout/stderr) and optional file output.
    Ensures log format includes timestamp, level, module, and message.
    
    Args:
        log_level: Optional logging level (e.g., logging.DEBUG). Defaults to INFO.
        log_file: Optional path to a log file. If provided, logs are written there.
    
    Returns:
        The configured root logger instance.
    """
    if log_level is None:
        log_level = logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates in repeated calls
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Define a consistent format
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Return a named logger for the project to ensure specific namespace usage
    return logging.getLogger('proj_560')
