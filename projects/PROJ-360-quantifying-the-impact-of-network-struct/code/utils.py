"""
Module: code/utils.py
Purpose: Utility functions for logging, retries, and seeding.
"""
import logging
import random
import time
import os
from typing import Callable, TypeVar, List, Any, Optional
from functools import wraps
from pathlib import Path

def setup_logging(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup a logger with file and console handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

T = TypeVar('T')

def retry_with_exponential_backoff(max_retries: int = 3, base_delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    Decorator to retry a function with exponential backoff.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    delay = base_delay * (2 ** attempt)
                    logging.getLogger(func.__module__).warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. Retrying in {delay}s..."
                    )
                    time.sleep(delay)
            logging.getLogger(func.__module__).error(f"Failed after {max_retries} retries: {last_exception}")
            raise last_exception
        return wrapper
    return decorator

def pin_seed(seed: int = 42):
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def fetch_with_retry(url: str, params: Optional[Dict] = None, timeout: int = 30) -> Optional[Dict]:
    """
    Simple fetch with retry logic (wrapper for requests.get).
    """
    import requests
    
    @retry_with_exponential_backoff()
    def _fetch():
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    try:
        return _fetch()
    except Exception as e:
        logging.error(f"Fetch failed: {e}")
        return None