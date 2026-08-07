import logging
import random
import time
import os
from typing import Callable, TypeVar, List, Any, Optional
from functools import wraps

T = TypeVar('T')

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> Callable[..., T]:
    """Decorator for retrying a function with exponential backoff."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        delay = base_delay
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
        raise RuntimeError("Max retries exceeded")
    return wrapper

def pin_seed(seed: int = 42):
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    # If numpy is available, pin its seed too
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    # If torch is available, pin its seed too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def fetch_with_retry(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """Fetch data with retry logic (wrapper for requests.get)."""
    import requests
    max_retries = 5
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                delay = base_delay * (2 ** attempt)
                logging.warning(f"Rate limited. Waiting {delay}s before retry {attempt + 1}/{max_retries}")
                time.sleep(delay)
                continue
            else:
                logging.error(f"API request failed with status {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error: {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(base_delay * (2 ** attempt))
    
    return None
