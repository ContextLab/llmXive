"""
Structured logging utilities for the statistical robustness pipeline.

Provides consistent log formatting, warning/error handling, and
integration with the project's configuration settings.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from src.utils.config import get_path, get_project_root

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Module-level logger instance
_logger: Optional[logging.Logger] = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger instance with consistent configuration.
    
    Args:
        name: Optional name for the logger. If None, uses project root name.
    
    Returns:
        Configured logging.Logger instance.
    """
    global _logger
    
    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(DEFAULT_LOG_LEVEL)
        
        # Clear existing handlers to avoid duplicates
        _logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(DEFAULT_LOG_LEVEL)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        _logger.addHandler(console_handler)
        
        # File handler - log to results directory
        try:
            log_dir = get_path("results")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "pipeline.log"
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            _logger.addHandler(file_handler)
        except Exception:
            # If log directory setup fails, continue with console only
            pass
    
    if name:
        return logging.getLogger(f"llmXive.{name}")
    return _logger


def log_warning(message: str, category: Optional[str] = None, module: Optional[str] = None) -> None:
    """
    Log a structured warning message.
    
    Args:
        message: The warning message text.
        category: Optional category (e.g., "DataQuality", "Statistical").
        module: Optional module name where the warning originated.
    """
    logger = get_logger(module)
    
    if category:
        structured_message = f"[{category}] {message}"
    else:
        structured_message = message
    
    logger.warning(structured_message)


def log_error(message: str, category: Optional[str] = None, module: Optional[str] = None, 
             exception: Optional[Exception] = None) -> None:
    """
    Log a structured error message.
    
    Args:
        message: The error message text.
        category: Optional category (e.g., "DataFetch", "Computation").
        module: Optional module name where the error originated.
        exception: Optional exception instance to include in the log.
    """
    logger = get_logger(module)
    
    if category:
        structured_message = f"[{category}] {message}"
    else:
        structured_message = message
    
    if exception:
        logger.error(structured_message, exc_info=True)
    else:
        logger.error(structured_message)


def log_info(message: str, module: Optional[str] = None) -> None:
    """
    Log an informational message.
    
    Args:
        message: The message text.
        module: Optional module name.
    """
    logger = get_logger(module)
    logger.info(message)


def log_debug(message: str, module: Optional[str] = None) -> None:
    """
    Log a debug message.
    
    Args:
        message: The message text.
        module: Optional module name.
    """
    logger = get_logger(module)
    logger.debug(message)


def configure_logging_for_task(task_name: str) -> logging.Logger:
    """
    Configure and return a logger specifically for a task.
    
    Args:
        task_name: Name of the task (e.g., "T005", "US1").
    
    Returns:
        Configured logger instance.
    """
    return get_logger(f"tasks.{task_name}")


def set_log_level(level: int, module: Optional[str] = None) -> None:
    """
    Set the log level for a specific module or all loggers.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.WARNING).
        module: Optional module name. If None, sets for all loggers.
    """
    if module:
        logger = get_logger(module)
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)
    else:
        global _logger
        if _logger:
            _logger.setLevel(level)
            for handler in _logger.handlers:
                handler.setLevel(level)
        # Also update root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)


# Convenience aliases
warn = log_warning
error = log_error
info = log_info
debug = log_debug