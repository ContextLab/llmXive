import logging
import time
from pathlib import Path
from typing import Optional

def setup_experiment_logging(log_path: str = "experiment.log") -> logging.Logger:
    """
    Configure error logging with timestamps to the specified log file.
    """
    # Ensure directory exists
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("experiment")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler with timestamp
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def log_error(logger: logging.Logger, message: str, exception: Optional[Exception] = None):
    """Log an error with optional exception details."""
    if exception:
        logger.error(f"{message}: {str(exception)}")
    else:
        logger.error(message)

def log_info(logger: logging.Logger, message: str):
    """Log an informational message."""
    logger.info(message)

def log_warning(logger: logging.Logger, message: str):
    """Log a warning message."""
    logger.warning(message)
