"""
Logging infrastructure for the project.
Provides a consistent logging interface across all modules.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

logger_instance = None
log_handler = None

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup the global logger.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        
    Returns:
        Configured logger instance
    """
    global logger_instance, log_handler
    
    if logger_instance is not None:
        return logger_instance
    
    # Create logger
    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
    
    logger_instance = logger
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Optional name for the logger (defaults to "llmXive")
        
    Returns:
        Logger instance
    """
    if logger_instance is None:
        setup_logging()
    
    if name:
        return logger_instance.getChild(name)
    return logger_instance

def reset_logging():
    """Reset the logging configuration."""
    global logger_instance
    logger_instance = None

# Convenience functions
def debug(msg: str):
    if logger_instance:
        logger_instance.debug(msg)

def info(msg: str):
    if logger_instance:
        logger_instance.info(msg)

def warning(msg: str):
    if logger_instance:
        logger_instance.warning(msg)

def error(msg: str):
    if logger_instance:
        logger_instance.error(msg)

def critical(msg: str):
    if logger_instance:
        logger_instance.critical(msg)

def exception(msg: str):
    if logger_instance:
        logger_instance.exception(msg)
