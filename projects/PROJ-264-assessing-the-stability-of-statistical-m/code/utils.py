"""
Utility functions for seeding, logging, and error handling.
"""
import logging
import os
import random
import sys
import traceback
from functools import wraps

def set_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
    except ImportError:
        pass

def setup_logging(level: int = logging.INFO):
    """Configure logging for the project."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

class PipelineError(Exception):
    """Custom exception for pipeline errors."""
    pass

def log_and_reraise(func):
    """Decorator to log exceptions and re-raise them."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger(func.__module__)
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise
    return wrapper

def safe_execute(func, default=None):
    """Execute a function and return default on error."""
    try:
        return func()
    except Exception:
        logger = logging.getLogger(__name__)
        logger.warning(f"Execution of {func.__name__} failed, returning default.")
        return default
