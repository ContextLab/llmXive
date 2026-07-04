"""
API utilities with exponential backoff for GitHub API calls.
Implements FR-006: ≤3 retries, ≥60-second delay.
"""

import time
import logging
import random
from typing import Callable, Any, Optional, TypeVar, Tuple
from functools import wraps

from .logging_utils import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 3
MIN_DELAY = 60  # seconds
MAX_DELAY = 300  # seconds

def exponential_backoff_delay(attempt: int, base_delay: int = MIN_DELAY) -> float:
    """
    Calculate delay with exponential backoff and jitter.
    
    Args:
        attempt: Current retry attempt (0-indexed)
        base_delay: Base delay in seconds
    
    Returns:
        Delay duration in seconds
    """
    # Exponential: base_delay * 2^attempt
    delay = base_delay * (2 ** attempt)
    
    # Add jitter (±10%)
    jitter = delay * 0.1 * (random.random() * 2 - 1)
    delay += jitter
    
    # Clamp to max delay
    delay = min(delay, MAX_DELAY)
    
    return max(delay, base_delay)

def retry_with_exponential_backoff(func: Callable) -> Callable:
    """
    Decorator to retry a function with exponential backoff.
    
    Implements FR-006: ≤3 retries, ≥60-second delay.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        last_exception = None
        
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    delay = exponential_backoff_delay(attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{MAX_RETRIES} for {func.__name__} "
                        f"after {delay:.1f}s delay due to: {str(e)}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Failed {func.__name__} after {MAX_RETRIES} attempts: {str(e)}"
                    )
        
        raise last_exception
    
    return wrapper

def fetch_with_backoff(url: str, timeout: int = 30) -> Tuple[bool, Optional[Any]]:
    """
    Fetch data from a URL with exponential backoff.
    
    Implements FR-006: ≤3 retries, ≥60-second delay.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
    
    Returns:
        Tuple of (success, data)
    """
    import urllib.request
    import urllib.error
    import json

    last_exception = None
    
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Research'})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                return True, data
        except urllib.error.HTTPError as e:
            if e.code == 403:  # Rate limit
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    delay = exponential_backoff_delay(attempt)
                    logger.warning(
                        f"Rate limit (403). Retry {attempt + 1}/{MAX_RETRIES} "
                        f"after {delay:.1f}s"
                    )
                    time.sleep(delay)
                else:
                    logger.error("Rate limit exceeded after all retries")
                    return False, None
            else:
                logger.error(f"HTTP Error {e.code}: {e.reason}")
                return False, None
        except urllib.error.URLError as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                delay = exponential_backoff_delay(attempt)
                logger.warning(
                    f"URL Error: {str(e)}. Retry {attempt + 1}/{MAX_RETRIES} "
                    f"after {delay:.1f}s"
                )
                time.sleep(delay)
            else:
                logger.error(f"URL Error after all retries: {str(e)}")
                return False, None
        except Exception as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                delay = exponential_backoff_delay(attempt)
                logger.warning(
                    f"Unexpected error: {str(e)}. Retry {attempt + 1}/{MAX_RETRIES} "
                    f"after {delay:.1f}s"
                )
                time.sleep(delay)
            else:
                logger.error(f"Unexpected error after all retries: {str(e)}")
                return False, None
    
    return False, None
