"""
Logging configuration module.

Implements T008: Error handling and logging infrastructure.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def configure_logging(log_file: Optional[str] = None, level: Optional[str] = None) -> None:
    """
    Configure global logging settings.
    
    Args:
        log_file: Optional path to a log file.
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    level = level or LOG_LEVEL
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    logging.basicConfig(
        level=numeric_level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.getLogger().addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)

def set_log_level(level: str) -> None:
    """Set the global log level."""
    numeric_level = getattr(logging, level.upper(), None)
    if isinstance(numeric_level, int):
        logging.getLogger().setLevel(numeric_level)

# Convenience functions
def debug(msg: str):
    logging.debug(msg)

def info(msg: str):
    logging.info(msg)

def warning(msg: str):
    logging.warning(msg)

def error(msg: str):
    logging.error(msg)

def critical(msg: str):
    logging.critical(msg)

# Initialize logging on module import
configure_logging()
