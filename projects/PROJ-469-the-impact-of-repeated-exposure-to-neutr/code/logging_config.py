"""
Logging infrastructure configuration for the llmXive research pipeline.

Provides centralized logging setup with:
- Console output with colored levels
- File output with rotation (logs/project.log)
- Structured error handling utilities
"""
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config import ensure_dirs

# Constants for log configuration
LOG_DIR = "logs"
LOG_FILE = "project.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Color codes for console output
COLORS = {
    "DEBUG": "\033[36m",      # Cyan
    "INFO": "\033[32m",       # Green
    "WARNING": "\033[33m",    # Yellow
    "ERROR": "\033[31m",      # Red
    "CRITICAL": "\033[35m",   # Magenta
    "RESET": "\033[0m",       # Reset
}

class ColorFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels in console output."""

    def format(self, record):
        log_color = COLORS.get(record.levelname, COLORS["RESET"])
        record.levelname = f"{log_color}{record.levelname}{COLORS['RESET']}"
        return super().format(record)

def setup_logging(log_level: str = "INFO", console: bool = True, file: bool = True) -> logging.Logger:
    """
    Configure the root logger with console and file handlers.
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console: Whether to log to console
        file: Whether to log to file
        
    Returns:
        The configured root logger
    """
    # Ensure log directory exists
    ensure_dirs([LOG_DIR])
    
    log_path = Path(LOG_DIR) / LOG_FILE
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_formatter = ColorFormatter(LOG_FORMAT, DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if file:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger that inherits from the root logger.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def log_exception(logger: logging.Logger, message: str = "An unhandled exception occurred") -> None:
    """
    Log the current exception with full traceback.
    
    Args:
        logger: Logger instance to use
        message: Custom message to log with the exception
    """
    import traceback
    exc_type, exc_value, exc_tb = sys.exc_info()
    if exc_type is not None:
        logger.error(f"{message}: {exc_value}", exc_info=True)
    else:
        logger.error(message)

def handle_critical_error(logger: logging.Logger, message: str = "Critical error encountered") -> None:
    """
    Log a critical error and exit the program.
    
    Args:
        logger: Logger instance to use
        message: Error message to log
    """
    logger.critical(message)
    log_exception(logger)
    sys.exit(1)
