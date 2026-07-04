"""
Logging infrastructure for the doomscrolling anxiety project.

Configures logging to write to `output/logs/` with:
- Timestamps
- Log levels
- Error tracking (stack traces on exceptions)
- Rotation (size-based)
"""
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from config import Configuration

# Ensure the log directory exists
LOG_DIR = Path("output/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None,
    error_log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Configure the root logger and return a named logger.
    
    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Path to the general log file. Defaults to output/logs/pipeline.log.
        error_log_file: Path to the error-specific log file. Defaults to output/logs/errors.log.
        
    Returns:
        A configured logger instance.
    """
    # Use provided paths or defaults
    if log_file is None:
        log_file = LOG_FILE
    if error_log_file is None:
        error_log_file = ERROR_LOG_FILE

    # Ensure directories exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    error_log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates in interactive environments
    if logger.handlers:
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # General log handler (RotatingFileHandler to prevent unbounded growth)
    # Max size 10MB, keep 5 backup files
    general_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    general_handler.setLevel(log_level)
    general_handler.setFormatter(formatter)
    logger.addHandler(general_handler)

    # Error log handler (only logs ERROR and CRITICAL)
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def get_logger(name: str = "doomscrolling") -> logging.Logger:
    """
    Get a logger with a specific name.
    
    Args:
        name: The name for the logger (e.g., module name).
        
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)

def main():
    """
    Demo function to test the logging setup.
    """
    logger = setup_logging()
    log = get_logger("test_logger")
    
    log.info("Logging infrastructure initialized successfully.")
    log.debug("This is a debug message.")
    log.warning("This is a warning message.")
    
    try:
        # Simulate an error
        1 / 0
    except Exception as e:
        log.exception("An error occurred during testing.")

    log.info("Test complete. Check output/logs/ for logs.")

if __name__ == "__main__":
    main()
