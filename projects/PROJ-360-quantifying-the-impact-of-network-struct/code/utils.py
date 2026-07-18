import logging
import random
import time
import os
from typing import Callable, TypeVar, List, Any, Optional
from functools import wraps
import sys

def setup_logging(name: str, log_file: str = "results/app.log") -> logging.Logger:
    """
    Setup logging for a module.
    Creates the log directory if it doesn't exist.
    """
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # Set to DEBUG to capture all levels

    # Avoid adding handlers multiple times if called repeatedly in same process
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

def pin_seed(seed: int) -> None:
    """
    Pin random seeds for reproducibility.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy and torch seeds are set in their respective modules if needed

T = TypeVar('T')

def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Callable[..., T]:
    """
    Decorator to retry a function with exponential backoff.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logging.getLogger(func.__name__).warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
        raise RuntimeError("Max retries exceeded") # Should not reach here
    return wrapper

def fetch_with_retry(func: Callable, *args, **kwargs) -> Any:
    """
    Wrapper to fetch with retry logic for network calls.
    """
    # This is a generic wrapper, specific logic should be in the caller or a more specific decorator
    pass
