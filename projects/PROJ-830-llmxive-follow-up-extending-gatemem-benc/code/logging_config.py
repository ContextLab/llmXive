import os
import sys
import logging
import random
from typing import Optional, Any
from datetime import datetime

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Set up logging configuration."""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

def pin_random_seed(seed: int = 42):
    """Pin random seed for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

class ErrorHandling:
    """Context manager for error handling."""
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"Error occurred: {exc_val}")
            return False
        return True

def verify_log_creation(log_file: str) -> bool:
    """Verify that a log file was created successfully."""
    return os.path.exists(log_file) and os.path.getsize(log_file) > 0
