import time
import random
import logging
from typing import Callable, Type, TypeVar, Optional, List, Any
from functools import wraps
import os

T = TypeVar('T')

logger = logging.getLogger("RetryLogic")

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> Callable[..., T]:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        func: The function to retry.
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        exponential_base: Base for exponential backoff calculation.
        jitter: Whether to add random jitter to the delay.
    
    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        delay = initial_delay
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == max_retries:
                    logger.error(f"Failed after {max_retries} retries: {str(e)}")
                    raise
                
                # Calculate next delay
                current_delay = min(delay, max_delay)
                if jitter:
                    current_delay += random.uniform(0, 0.1 * current_delay)
                
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {current_delay:.2f}s...")
                time.sleep(current_delay)
                delay *= exponential_base

        # Should not reach here, but just in case
        raise last_exception
    
    return wrapper

def retry_download(
    url: str,
    destination: str,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0
):
    """
    Wrapper specifically for download operations with retry logic.
    
    Args:
        url: URL to download from.
        destination: Local path to save the file.
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
    
    Raises:
        RuntimeError: If download fails after all retries.
    """
    import requests
    from pathlib import Path

    @retry_with_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay
    )
    def _download():
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if not os.path.exists(destination):
            raise FileNotFoundError(f"Downloaded file not found at {destination}")
        
        logger.info(f"Successfully downloaded {url} to {destination}")
        return destination

    return _download()
