import logging
import os
import random
import sys
from datetime import datetime
from typing import Optional, Union

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Creates or retrieves a logger with consistent formatting.
    """
    logger_name = name or __name__
    logger = logging.getLogger(logger_name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    
    logger.addHandler(ch)
    return logger

def set_seeds(seed: int = 42) -> None:
    """
    Sets random seeds for reproducibility.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy and torch seeds set in their respective modules if imported

def get_seed() -> int:
    """
    Returns the current random seed (default 42).
    """
    return 42

def main():
    logger = get_logger()
    logger.info("Logging module initialized.")

if __name__ == "__main__":
    main()
