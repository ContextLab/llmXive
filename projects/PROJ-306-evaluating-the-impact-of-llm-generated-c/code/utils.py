import time
import random
from typing import Callable, TypeVar, Optional, Any, Tuple, Dict
from functools import wraps
import logging

T = TypeVar('T')

def exponential_backoff_retry(max_retries: int = 3, base_wait: float = 1.0, max_wait: float = 60.0):
    """
    Decorator for retrying a function with exponential backoff.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    wait_time = min(base_wait * (2 ** attempt) + random.uniform(0, 1), max_wait)
                    logging.warning(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. Retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
            logging.error(f"All {max_retries} attempts failed for {func.__name__}.")
            raise last_exception
        return wrapper
    return decorator

def retry_with_backoff(func: Callable, max_retries: int = 3, base_wait: float = 1.0):
    """
    Procedural retry logic for functions that might be rate-limited.
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            wait_time = base_wait * (2 ** attempt)
            logging.warning(f"Retry {attempt + 1}/{max_retries} failed: {e}. Waiting {wait_time}s.")
            time.sleep(wait_time)
    raise last_exception

def safe_get(d: Dict, key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary, handling nested keys with dot notation.
    """
    if not isinstance(d, dict):
        return default
    
    keys = key.split('.')
    current = d
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    return current

def format_bytes(num_bytes: int) -> str:
    """
    Format a number of bytes into a human-readable string.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"
