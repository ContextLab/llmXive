import logging
import os
from pathlib import Path
from typing import Optional

# Ensure the project root is in the path if running as a script
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DATA_RESULTS_DIR = _PROJECT_ROOT / "data" / "results"

def _ensure_log_directory():
    """Create the log directory if it does not exist."""
    _DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieve or create a logger instance.
    
    Args:
        name: The name of the logger.
        
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    # Avoid adding duplicate handlers if called multiple times in same process
    if not logger.handlers:
        _ensure_log_directory()
        log_file_path = _DATA_RESULTS_DIR / "processing.log"
        
        # Configure file handler
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        
        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Set level
        logger.setLevel(logging.DEBUG)
        
    return logger

def setup_logging(log_level: Optional[int] = None) -> None:
    """
    Configure the root logger and ensure the logging directory exists.
    
    Args:
        log_level: Optional logging level (e.g., logging.DEBUG). 
                   If None, defaults to DEBUG.
    """
    _ensure_log_directory()
    log_file_path = _DATA_RESULTS_DIR / "processing.log"
    
    if log_level is None:
        log_level = logging.DEBUG
        
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to prevent duplicates in interactive sessions
    if root_logger.handlers:
        root_logger.handlers.clear()
        
    # File handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup
    logger = get_logger()
    logger.info("Logging infrastructure initialized. Log file: %s", log_file_path)