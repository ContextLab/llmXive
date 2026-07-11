"""
Logging configuration for the project.
"""
import logging
import sys
from typing import Optional

def configure_root_logger(level: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger with a standard format.

    Args:
        level: Log level string (e.g., 'INFO', 'DEBUG'). Defaults to 'INFO'.

    Returns:
        The configured root logger.
    """
    if level is None:
        level = "INFO"

    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid adding duplicate handlers if called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    return root_logger

def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Setup a named logger.

    Args:
        name: Name of the logger.
        level: Log level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    else:
        logger.setLevel(logging.INFO)
    return logger
