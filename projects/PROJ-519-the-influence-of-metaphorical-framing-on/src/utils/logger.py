"""
Logging utility module.
Provides centralized logging configuration for the project.
"""
import logging
import sys
from typing import Optional

def setup_logger(
    name: str = "llmXive",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Name of the logger.
        level: Logging level.
        log_file: Optional path to a log file.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get a logger instance by name.
    If the logger hasn't been set up, it will use default settings.
    """
    return logging.getLogger(name)

# Default logger instance for immediate use
logger = setup_logger()
__all__ = ['setup_logger', 'get_logger', 'logger']