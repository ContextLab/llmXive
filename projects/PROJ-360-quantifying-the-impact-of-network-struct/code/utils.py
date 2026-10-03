import logging
import random
import time
import os
from typing import Callable, TypeVar, List, Any, Optional
from functools import wraps
import numpy as np

T = TypeVar('T')

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("llmXive")

def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
) -> Callable[..., T]:
    """Decorator to retry a function with exponential backoff."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        delay = base_delay
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logging.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {delay:.1f}s")
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
                else:
                    logging.error(f"Failed after {max_retries} retries: {e}")
                    raise
        raise last_exception
    return wrapper

def pin_seed(seed: int = 42) -> None:
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    logging.info(f"Random seeds pinned to {seed}")

def fetch_with_retry(
    url: str,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    timeout: int = 30,
    max_retries: int = 5
) -> Optional[dict]:
    """Fetch data from URL with retry logic."""
    import requests
    retry_func = retry_with_exponential_backoff(
        requests.get,
        max_retries=max_retries,
        exceptions=(requests.RequestException,)
    )
    try:
        response = retry_func(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return None
