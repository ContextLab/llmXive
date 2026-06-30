import logging
import os
from pathlib import Path
from typing import Optional
from config import get_logs_dir, get_log_file_path as config_get_log_file_path, get_error_log_file_path as config_get_error_log_file_path, get_manipulation_error_log_path as config_get_manipulation_error_log_path

def get_logger(name: str = "llmXive", level: Optional[int] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    if level is None:
        log_level_str = os.getenv("LOG_LEVEL", "INFO")
        level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    logger.setLevel(level)
    
    # Create handlers
    log_file = config_get_log_file_path()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    error_file = config_get_error_log_file_path()
    error_file.parent.mkdir(parents=True, exist_ok=True)
    error_handler = logging.FileHandler(error_file)
    error_handler.setLevel(logging.ERROR)
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger

def get_log_file_path() -> Path:
    """Return the path for the general application log file."""
    return config_get_log_file_path()

def get_error_log_file_path() -> Path:
    """Return the path for the general error log file."""
    return config_get_error_log_file_path()

def get_manipulation_error_log_path() -> Path:
    """Return the path for the specific manipulation error log file."""
    return config_get_manipulation_error_log_path()