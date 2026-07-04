import time
import logging
from typing import Callable, TypeVar, Optional, Tuple, Any
from functools import wraps
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

T = TypeVar('T')

def calculate_backoff_delay(retry_count: int, base_delay: float = 60.0, max_delay: float = 300.0) -> float:
    """
    Calculate exponential backoff delay.
    Delay = min(base_delay * 2^retry_count, max_delay)
    Ensures base delay is at least 60 seconds as per requirements.
    """
    delay = min(base_delay * (2 ** retry_count), max_delay)
    # Add jitter (±10%)
    import random
    jitter = delay * 0.1 * (random.random() - 0.5)
    return max(0, delay + jitter)

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 60.0,
    max_delay: float = 300.0
) -> Callable[..., T]:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        func: The function to wrap.
        max_retries: Maximum number of retry attempts (default 3, ≤3 as required).
        base_delay: Base delay in seconds (default 60.0, ≥60s as required).
        max_delay: Maximum delay cap in seconds.
    
    Returns:
        Wrapped function with retry logic.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        last_exception = None
        
        for retry_count in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except RequestException as e:
                last_exception = e
                if retry_count < max_retries:
                    delay = calculate_backoff_delay(retry_count, base_delay, max_delay)
                    logger.warning(
                        f"Request failed: {e}. "
                        f"Retrying in {delay:.1f}s (attempt {retry_count + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Request failed after {max_retries} retries: {e}")
                    raise
        raise last_exception
    return wrapper

def handle_github_rate_limit(response: requests.Response) -> None:
    """Handle GitHub rate limit responses (403)."""
    if response.status_code == 403 and 'rate limit' in response.text.lower():
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        if reset_time > 0:
            wait_time = max(1, reset_time - int(time.time()))
            logger.warning(f"GitHub rate limit exceeded. Waiting {wait_time} seconds.")
            time.sleep(wait_time)
        else:
            # Wait a safe default
            logger.warning("GitHub rate limit exceeded. Waiting 60 seconds.")
            time.sleep(60)
    else:
        logger.warning(f"Unexpected 403 response: {response.text}")

@retry_with_backoff(max_retries=3, base_delay=60.0, max_delay=300.0)
def github_api_request(
    method: str,
    url: str,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    **kwargs
) -> requests.Response:
    """
    Make a GitHub API request with automatic retry on rate limits.
    Uses ≤3 retries and ≥60s base delay as per task requirements.
    """
    response = requests.request(method, url, headers=headers, params=params, **kwargs)
    
    if response.status_code == 403:
        handle_github_rate_limit(response)
        # Retry after handling
        return github_api_request(method, url, headers, params, **kwargs)
        
    response.raise_for_status()
    return response

def fetch_with_backoff(
    request_func: Callable,
    *args,
    max_retries: int = 3,
    base_delay: float = 60.0,
    max_delay: float = 300.0,
    **kwargs
) -> requests.Response:
    """
    Execute a request function with exponential backoff and rate limit handling.
    
    Args:
        request_func: The function to call (e.g., requests.get).
        max_retries: Maximum retries (default 3, ≤3 as required).
        base_delay: Base delay in seconds (default 60.0, ≥60s as required).
        max_delay: Maximum delay cap.
    
    Returns:
        The response object from the successful request.
    
    Raises:
        RequestException: If all retries are exhausted.
    """
    last_exception = None
    
    for retry_count in range(max_retries + 1):
        try:
            response = request_func(*args, **kwargs)
            
            if response.status_code == 403:
                handle_github_rate_limit(response)
                if retry_count < max_retries:
                    delay = calculate_backoff_delay(retry_count, base_delay, max_delay)
                    logger.warning(f"Rate limited. Waiting {delay:.1f}s before retry.")
                    time.sleep(delay)
                    continue
                else:
                    raise RequestException("Rate limit exceeded after all retries")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            last_exception = e
            if retry_count < max_retries:
                delay = calculate_backoff_delay(retry_count, base_delay, max_delay)
                logger.warning(
                    f"Request failed: {e}. "
                    f"Retrying in {delay:.1f}s (attempt {retry_count + 1}/{max_retries})"
                )
                time.sleep(delay)
            else:
                logger.error(f"Request failed after {max_retries} retries: {e}")
                raise
    
    raise last_exception