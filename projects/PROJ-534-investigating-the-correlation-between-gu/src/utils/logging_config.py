"""
Logging configuration for the gut microbiome and cognitive flexibility pipeline.

This module sets up the root logger to write logs to `logs/pipeline.log` and
optionally to the console with appropriate formatting.
"""
import logging
import sys
from pathlib import Path
import os

# Ensure logs directory exists
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "pipeline.log"

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger.
    
    Args:
        log_level: The logging level (default: INFO).
        
    Returns:
        The configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates in interactive environments
    if logger.handlers:
        logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(log_level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger (usually __name__).
        
    Returns:
        A logger instance.
    """
    return logging.getLogger(name)

# Initialize logging when this module is imported
# This ensures logging is ready for all subsequent imports
setup_logging()