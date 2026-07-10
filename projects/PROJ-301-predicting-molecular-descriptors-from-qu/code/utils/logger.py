"""
Logger configuration and error handling infrastructure for the llmXive pipeline.

This module provides a centralized logging setup that ensures consistent
log formatting, file rotation, and error handling across the project.
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from datetime import datetime

# Global logger instance
_logger: Optional[logging.Logger] = None
_setup_called: bool = False

# Default log configuration
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_DIR = "data/logs"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5


def setup_logger(
    name: str = "llmXive",
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: str = DEFAULT_LOG_DIR,
    log_file: Optional[str] = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    enable_console: bool = True,
    enable_file: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger instance with file and console handlers.
    
    Args:
        name: Logger name (usually __name__ from caller)
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_dir: Directory for log files (relative to project root)
        log_file: Optional specific log filename. If None, uses auto-generated name.
        max_bytes: Max size before log rotation (default: 10MB)
        backup_count: Number of backup files to keep
        enable_console: Whether to add a console handler
        enable_file: Whether to add a file handler
    
    Returns:
        Configured logger instance
    
    Raises:
        ValueError: If log directory cannot be created
    """
    global _logger, _setup_called
    
    # Prevent reconfiguration if already set up
    if _setup_called and _logger is not None:
        return _logger
    
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Determine log filename
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"pipeline_{timestamp}.log"
    
    log_file_path = log_path / log_file
    
    # Create or get the logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT
    )
    
    # Add console handler if requested
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if requested
    if enable_file:
        try:
            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8"
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            # Fallback to console-only if file logging fails
            logger.warning(f"Failed to create file handler: {e}. Using console only.")
    
    # Mark as configured
    _logger = logger
    _setup_called = True
    
    return logger


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get the configured logger instance.
    
    If the logger hasn't been set up yet, it will be initialized with defaults.
    
    Args:
        name: Logger name to retrieve or create
    
    Returns:
        Logger instance
    """
    global _logger, _setup_called
    
    if not _setup_called:
        return setup_logger(name)
    
    return logging.getLogger(name)


def log_exception(
    logger: Optional[logging.Logger] = None,
    message: str = "An unexpected error occurred",
    exc_info: bool = True,
    level: int = logging.ERROR
) -> None:
    """
    Log an exception with full traceback information.
    
    Args:
        logger: Logger instance to use. If None, uses default logger.
        message: Log message to include with the exception
        exc_info: Whether to include exception traceback
        level: Logging level for the exception
    """
    log = logger or get_logger()
    log.log(level, message, exc_info=exc_info)


def configure_logging_for_pipeline(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: str = DEFAULT_LOG_DIR
) -> logging.Logger:
    """
    Configure logging specifically for pipeline execution with appropriate
    handlers and levels.
    
    Args:
        log_level: Logging level for the pipeline
        log_dir: Directory for pipeline logs
    
    Returns:
        Configured pipeline logger
    """
    return setup_logger(
        name="llmXive.pipeline",
        log_level=log_level,
        log_dir=log_dir,
        enable_console=True,
        enable_file=True
    )


# Convenience function for quick logging setup
def init_default_logging() -> logging.Logger:
    """
    Initialize logging with default settings.
    
    Returns:
        Configured default logger
    """
    return setup_logger()