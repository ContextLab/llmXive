"""
Standardized logging configuration for the llmXive pipeline.

This module provides a unified logging setup to ensure consistent
formatting, level management, and output destinations across all
project modules.

Usage:
    from data.logging_config import configure_logging, get_logger
  
    configure_logging(level=logging.INFO)
    logger = get_logger(__name__)
    logger.info("This message will be formatted consistently.")
"""
import logging
import sys
from typing import Optional
from pathlib import Path

# Standardized format string: [Timestamp] [Level] [Module] Message
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Ensure log directory exists if logging to file
_LOG_DIR = Path("projects/PROJ-512-predicting-molecular-permeability-of-pol/code/logs")
_LOG_FILE = _LOG_DIR / "pipeline.log"

def configure_logging(
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_file: Optional[Path] = None,
    enable_console: bool = True
) -> None:
    """
    Configure the root logger with standardized formatting.
    
    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_to_file: Whether to write logs to a file.
        log_file: Path to the log file. Defaults to project logs directory.
        enable_console: Whether to output logs to stdout.
    """
    # Create handlers
    handlers = []
    
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
        handlers.append(console_handler)
    
    if log_to_file:
        target_file = log_file or _LOG_FILE
        target_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(target_file))
        file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
        handlers.append(file_handler)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to prevent duplicates on re-configuration
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    for handler in handlers:
        root_logger.addHandler(handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    The logger inherits the configuration from the root logger.
    
    Args:
        name: The name of the logger (typically __name__).
    
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)

def set_global_log_level(level: int) -> None:
    """
    Update the global log level for all existing loggers.
    
    Args:
        level: The new logging level.
    """
    logging.getLogger().setLevel(level)
