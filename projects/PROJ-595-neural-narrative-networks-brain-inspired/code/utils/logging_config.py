import logging
import os
import sys
from pathlib import Path
from typing import Optional

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline.log"

class ErrorFormatter(logging.Formatter):
    """Custom formatter that prefixes error codes."""
    def format(self, record):
        if record.levelno >= logging.ERROR:
            record.msg = f"[E{record.lineno:03d}] {record.msg}"
        return super().format(record)

def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Initialize a logger that writes to logs/pipeline.log and prints to stderr.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Console handler for errors
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_formatter = ErrorFormatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def log_error(code: str, message: str):
    """Log an error with specific error code."""
    logger = get_logger()
    logger.error(f"[{code}] {message}")

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
