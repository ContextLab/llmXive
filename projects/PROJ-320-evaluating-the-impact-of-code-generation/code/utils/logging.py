"""
logging.py

Centralized logging configuration with file rotation and PII filtering.
"""
import logging
import os
import re
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Dict, Any

from utils.config import get_path

# PII patterns
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
GITHUB_USER_PATTERN = re.compile(r'\b(?:@|\s)([A-Za-z0-9]+-?[A-Za-z0-9]*)\b')

class PIIFilter(logging.Filter):
    """Filter to mask PII in log messages."""
    
    def filter(self, record):
        msg = record.getMessage()
        # Mask emails
        msg = EMAIL_PATTERN.sub('[EMAIL_REDACTED]', msg)
        # Mask GitHub usernames (simple heuristic)
        msg = GITHUB_USER_PATTERN.sub(' [USER_REDACTED]', msg)
        record.msg = msg
        return True

def get_log_directory() -> Path:
    """Get the directory for log files."""
    log_dir = get_path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    enable_pii_filter: bool = True
) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level (e.g., logging.INFO).
        log_file: Optional filename for the log file (relative to data/logs).
        enable_pii_filter: Whether to enable PII masking.
        
    Returns:
        The root logger instance.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_dir = get_log_directory()
        file_path = log_dir / log_file
        
        # Use RotatingFileHandler to prevent log files from growing indefinitely
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024, # 10 MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        
        if enable_pii_filter:
            file_handler.addFilter(PIIFilter())
        
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    Assumes logging has been setup via setup_logging().
    
    Args:
        name: Logger name (usually __name__).
        
    Returns:
        Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # If not configured yet, setup basic logging
        setup_logging()
    return logger

def rotate_logs():
    """
    Trigger log rotation.
    Useful for scheduled tasks or cleanup.
    """
    log_dir = get_log_directory()
    for handler in logging.getLogger().handlers:
        if isinstance(handler, RotatingFileHandler):
            handler.doRollover()

def init_logger_for_script(script_name: str) -> logging.Logger:
    """
    Initialize logging specifically for a script.
    
    Args:
        script_name: Name of the script (e.g., 'fetch_github').
        
    Returns:
        Configured logger.
    """
    log_file = f"{script_name}.log"
    setup_logging(log_file=log_file)
    return get_logger(script_name)

def main():
    """Test logging setup."""
    logger = init_logger_for_script("logging_test")
    logger.info("Logging setup test.")
    logger.warning("This is a warning.")
    logger.error("This is an error.")
    logger.info("User email: test@example.com should be masked.")

if __name__ == "__main__":
    main()
