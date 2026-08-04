"""
Structured logging infrastructure.
"""
import logging
import sys
import os
from typing import Optional
from datetime import datetime

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """
    Setup logging configuration.

    Args:
        level: Logging level.
        log_file: Optional log file path.
    """
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)

def configure_root_logger(level: int = logging.INFO):
    """
    Configure the root logger.

    Args:
        level: Logging level.
    """
    logging.getLogger().setLevel(level)
