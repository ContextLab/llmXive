import logging
import os
from pathlib import Path
from config import LOG_LEVEL, LOG_FORMAT, LOGS_DIR

def setup_logging():
    """
    Configure the root logger.
    """
    # Ensure logs directory exists
    log_path = Path(LOGS_DIR)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Define handlers
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    
    file_handler = logging.FileHandler(log_path / "pipeline.log")
    file_handler.setLevel(LOG_LEVEL)
    
    # Define formatter
    formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    """
    return logging.getLogger(name)