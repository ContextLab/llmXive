"""
Logging setup module.
Provides a consistent logging configuration for the project.
"""
import logging
import sys
import os
from datetime import datetime
from typing import Optional

def setup_logging(module_name: str = "project", log_level: int = logging.INFO) -> logging.Logger:
    """
    Setup and return a logger with standard formatting.
    Creates a logs directory if it doesn't exist.
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(log_level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Create logs directory
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{module_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(log_level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger