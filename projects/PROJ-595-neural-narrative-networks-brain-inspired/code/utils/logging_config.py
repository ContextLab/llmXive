import logging
import os
import sys
from pathlib import Path
from typing import Optional

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline.log"

class ErrorFormatter(logging.Formatter):
    """Custom formatter that prefixes error codes to error messages."""
    def format(self, record):
        # If the message already contains an explicit error code like [E001],
        # preserve it. Otherwise, generate a generic error code based on line number
        # if no explicit code was provided by the caller.
        if not record.msg.startswith("[E"):
            # Use the line number of the caller (2 levels up) as a fallback code
            # This ensures we always have a code, but explicit codes take precedence
            code = f"E{record.lineno:03d}"
            record.msg = f"[{code}] {record.msg}"
        return super().format(record)

def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Initialize a logger that writes to logs/pipeline.log and prints errors to stderr.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # File handler - logs everything at DEBUG level and above
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Console handler for errors and above - prints to stderr
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_formatter = ErrorFormatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def log_error(code: str, message: str):
    """Log an error with a specific error code to both file and stderr.
    
    Args:
        code: Error code string (e.g., "E001")
        message: Error message
    """
    logger = get_logger()
    # Format the message with the explicit error code
    formatted_msg = f"[{code}] {message}"
    logger.error(formatted_msg)

# Convenience functions
def info(msg: str):
    get_logger().info(msg)

def debug(msg: str):
    get_logger().debug(msg)

def warning(msg: str):
    get_logger().warning(msg)

def error(msg: str):
    get_logger().error(msg)

def critical(msg: str):
    get_logger().critical(msg)