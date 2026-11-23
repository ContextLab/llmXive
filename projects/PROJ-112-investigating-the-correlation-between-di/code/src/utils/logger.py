"""
Standardized logging configuration for the llmXive research pipeline.
Provides a consistent interface for creating loggers across the project.
"""
import logging
import os
from pathlib import Path
from typing import Optional

# Global cache to prevent re-configuring handlers
_logger_cache = {}

def reset_logger_cache():
    """Reset the logger cache, useful for testing."""
    global _logger_cache
    _logger_cache = {}
    logging.getLogger().handlers = []
    logging.getLogger().disabled = False

def get_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: The name of the logger (usually __name__).
        log_file: Optional path to a log file. If provided, logs are written to file.
        level: Logging level (default: INFO).
    
    Returns:
        A configured logging.Logger instance.
    """
    if name in _logger_cache:
        return _logger_cache[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times in same process
    if logger.handlers:
        _logger_cache[name] = logger
        return logger

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger_cache[name] = logger
    return logger

import sys
