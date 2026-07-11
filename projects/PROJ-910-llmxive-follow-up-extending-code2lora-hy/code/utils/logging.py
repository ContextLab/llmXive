"""
Logging utilities for the llmXive pipeline.

Defines warning handlers and logging setup as required by FR-007.
This module provides the handler but does not implement the skip logic itself;
that logic is implemented in the specific module (e.g., ast_parser.py) using this handler.
"""
import logging
import sys
from pathlib import Path


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger for the project.
    
    Args:
        log_level: The logging level to set (default: INFO).
        
    Returns:
        The configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.
    
    Args:
        name: The name of the logger (usually __name__).
        
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)


# Warning handler for FR-007 (Setup Only)
# This handler is used to log warnings when malformed files are encountered.
# The actual logic to skip files and call this handler is implemented in T016.
def warning_handler(message: str) -> None:
    """
    Log a warning message using the project's logging configuration.
    
    Args:
        message: The warning message to log.
    """
    logger = get_logger(__name__)
    logger.warning(message)