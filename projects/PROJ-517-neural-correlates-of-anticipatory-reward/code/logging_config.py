import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_level: int = logging.INFO, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Configure root logger with console and optional file handlers.
    
    Args:
        log_level: The logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file.
    
    Returns:
        The root logger instance.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger.
    
    Returns:
        A logger instance.
    """
    return logging.getLogger(name)
