import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure logs directory exists
LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(exist_ok=True)

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger with file and console handlers.
    
    Args:
        level: Logging level (default: INFO)
    
    Returns:
        Configured root logger
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(LOGS_DIR / 'pipeline.log')
    file_handler.setLevel(level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_error_to_file(file_path: str, timestamp: str, row_id: str, reason: str) -> None:
    """
    Log a salience computation error to the specified file.
    
    This function implements the error logging requirement for T016:
    - Appends a line to the error log file
    - Format: timestamp, row_id, reason
    
    Args:
        file_path: Path to the error log file (e.g., 'logs/salience_errors.log')
        timestamp: ISO format timestamp string
        row_id: Unique identifier for the failed row
        reason: Description of the failure reason
    """
    # Ensure directory exists
    log_dir = os.path.dirname(file_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Append error entry
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp},{row_id},{reason}\n")
    
    # Also log to the main logger for visibility
    logger = get_logger(__name__)
    logger.error(f"Salience error logged: row_id={row_id}, reason={reason}")

# Initialize logging on module import
setup_logging()
