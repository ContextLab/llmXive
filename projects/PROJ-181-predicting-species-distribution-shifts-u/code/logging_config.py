"""
Logging Configuration Module.
Sets up the logging infrastructure to write to logs/ directory.
"""
import logging
import os
import sys
from pathlib import Path
from config import LOGS_DIR

def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Relative filename for the log file (defaults to name.log)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler (if log_file specified)
    if log_file:
        log_path = LOGS_DIR / log_file
        fh = logging.FileHandler(log_path, mode='a')
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves or creates a logger with the given name.
    """
    return logging.getLogger(name)
