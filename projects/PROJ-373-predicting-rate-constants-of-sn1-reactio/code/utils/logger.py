"""
Logging utility for the project.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging to console and optionally to a file.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates in some environments
    logger.handlers = []
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler if specified
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

def get_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Get a logger with the specified name.
    If log_file is provided, it will log to that file as well.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        setup_logging(log_file)
    return logger
