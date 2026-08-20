"""
Logging infrastructure for the llmXive statistical analysis pipeline.

This module provides a centralized logging configuration that ensures:
- Consistent log formatting across all project components
- Log file rotation and persistence in the state directory
- Console output for interactive debugging
- Proper integration with the project's configuration system

Usage:
    from src.utils.logging import get_logger, set_log_level
    
    logger = get_logger(__name__)
    logger.info("Processing started")
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import project configuration utilities
try:
    from src.utils.config import get_state_root, get_project_root
except ImportError:
    # Fallback for standalone execution or testing
    def get_state_root():
        return Path.cwd() / "state"
    
    def get_project_root():
        return Path.cwd()

# Module-level logger instance
_project_logger: Optional[logging.Logger] = None

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

def _ensure_log_directory() -> Path:
    """Ensure the log directory exists in the state folder."""
    state_root = get_state_root()
    log_dir = state_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def _get_log_filename() -> str:
    """Generate a timestamped log filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"pipeline_{timestamp}.log"

def _create_console_handler(level: int = logging.INFO) -> logging.StreamHandler:
    """Create a console handler with standard formatting."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT)
    handler.setFormatter(formatter)
    return handler

def _create_file_handler(level: int = logging.DEBUG) -> logging.FileHandler:
    """Create a file handler with rotation for log persistence."""
    log_dir = _ensure_log_directory()
    log_file = log_dir / _get_log_filename()
    
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        DATE_FORMAT
    )
    handler.setFormatter(formatter)
    return handler

def _create_project_logger(name: str) -> logging.Logger:
    """
    Create and configure the project logger with both console and file handlers.
    
    Args:
        name: The name of the logger (typically __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set to lowest level, handlers filter
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Add console handler (INFO and above)
    console_handler = _create_console_handler(logging.INFO)
    logger.addHandler(console_handler)
    
    # Add file handler (DEBUG and above)
    file_handler = _create_file_handler(logging.DEBUG)
    logger.addHandler(file_handler)
    
    # Add a critical error handler that writes to stderr
    critical_handler = logging.StreamHandler(sys.stderr)
    critical_handler.setLevel(logging.CRITICAL)
    critical_formatter = logging.Formatter(
        "CRITICAL ERROR: %(message)s",
        DATE_FORMAT
    )
    critical_handler.setFormatter(critical_formatter)
    logger.addHandler(critical_handler)
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger for the given module name.
    
    Args:
        name: Module name (defaults to 'llmXive' if not provided)
    
    Returns:
        Configured logger instance
    """
    if name is None:
        name = "llmXive"
    
    logger = logging.getLogger(name)
    
    # If logger has no handlers, configure it
    if not logger.handlers:
        logger = _create_project_logger(name)
    
    return logger

def set_log_level(level: str) -> None:
    """
    Set the log level for all project loggers.
    
    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Raises:
        ValueError: If the level string is not valid
    """
    level_upper = level.upper()
    if level_upper not in LOG_LEVELS:
        raise ValueError(
            f"Invalid log level: {level}. "
            f"Valid levels: {', '.join(LOG_LEVELS.keys())}"
        )
    
    numeric_level = LOG_LEVELS[level_upper]
    
    # Update all existing loggers
    for logger_name in logging.root.manager.loggerDict:
        if logger_name.startswith("llmXive") or logger_name.startswith("src"):
            logger = logging.getLogger(logger_name)
            logger.setLevel(numeric_level)
            for handler in logger.handlers:
                handler.setLevel(numeric_level)

def setup_project_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Initialize the project logging infrastructure.
    
    This should be called early in the application lifecycle to ensure
    all subsequent logging is properly configured.
    
    Args:
        log_level: Initial log level (default: INFO)
    
    Returns:
        The main project logger
    """
    # Set root logger level to catch all logs
    logging.root.setLevel(logging.DEBUG)
    
    # Set the project log level
    set_log_level(log_level)
    
    # Create and return the main logger
    global _project_logger
    _project_logger = get_logger("llmXive")
    
    _project_logger.info("Logging infrastructure initialized")
    _project_logger.debug(f"Log directory: {_ensure_log_directory()}")
    
    return _project_logger

# Convenience function for quick access
def log_message(level: str, message: str, module_name: str = "llmXive") -> None:
    """
    Log a message at the specified level.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Message to log
        module_name: Name of the module logging the message
    """
    logger = get_logger(module_name)
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message)
