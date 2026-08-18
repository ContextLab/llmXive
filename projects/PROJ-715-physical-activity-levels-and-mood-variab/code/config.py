import os
import random
import logging
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Random seed
RANDOM_SEED = 42

# Constants
MISSINGNESS_THRESHOLD = 0.5

# OSF DOI for StudentLife dataset
# Note: The actual DOI string is a placeholder as per the task description's "xxxx-xxxx"
# In a real scenario, this would be the actual DOI, e.g., "10.17605/OSF.IO/XXXXX"
OSF_DOI = "10.17605/OSF.IO/XXXXX" 

def set_random_seed(seed: int = RANDOM_SEED):
    """Set random seed for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def init_logger(name: str = "llmXive", level: int = logging.INFO) -> logging.Logger:
    """Initialize a logger with standard formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_path(*args) -> str:
    """
    Flexible path construction utility.
    Accepts:
      - get_path('data/processed', 'file.csv')  -> project_root/data/processed/file.csv
      - get_path('data', 'processed', 'file.csv') -> project_root/data/processed/file.csv
      - get_path('data', 'processed') -> project_root/data/processed
    """
    # If only one argument and it's a string with separators, treat as relative path
    if len(args) == 1 and isinstance(args[0], str) and '/' in args[0]:
        parts = [args[0]]
    else:
        parts = [str(p) for p in args]
    
    # Join parts
    relative_path = os.path.join(*parts)
    full_path = PROJECT_ROOT / relative_path
    
    return str(full_path)
