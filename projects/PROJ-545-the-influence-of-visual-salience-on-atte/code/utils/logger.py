import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure the logger module can be imported
# This file is referenced in the API surface but may not have been fully implemented

def setup_logging(log_level: str = 'INFO', log_file: Optional[str] = None) -> logging.Logger:
    """
    Sets up logging configuration for the project.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. If None, logs to console only.
        
    Returns:
        The root logger instance.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(console_formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Gets a logger instance with the given name.
    
    Args:
        name: The name of the logger. If None, returns the root logger.
        
    Returns:
        The logger instance.
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)

def log_error_to_file(message: str, file: str = 'error.log'):
    """
    Logs an error message to a specific file.
    
    Args:
        message: The error message to log.
        file: The filename to log to (relative to project root).
    """
    log_path = Path(file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_path, 'a') as f:
        f.write(f"[{timestamp}] ERROR: {message}\n")