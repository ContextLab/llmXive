"""
Retry logic with exponential backoff for external API calls.
"""
import time
import random
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Any, Optional, Union
from requests.exceptions import RequestException, Timeout, ConnectionError
import os

logger = logging.getLogger(__name__)


def calculate_backoff(retry_count: int, backoff_factor: float = 2.0, max_backoff: float = 60.0) -> float:
    """
    Calculate the backoff time for a given retry count.
    
    Args:
        retry_count: The current retry attempt number (0-indexed).
        backoff_factor: The base factor for exponential backoff.
        max_backoff: Maximum seconds to wait.
        
    Returns:
        float: The number of seconds to wait.
    """
    # Exponential backoff: base * (2 ^ retry_count)
    # Add jitter to prevent thundering herd
    jitter = random.uniform(0.1, 0.5)
    wait_time = backoff_factor * (2 ** retry_count) + jitter
    return min(wait_time, max_backoff)


def retry_with_backoff(
    func: Callable,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    max_backoff: float = 60.0,
    logger_name: Optional[str] = None
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        func: The function to wrap.
        exceptions: Tuple of exception types to catch and retry.
        max_retries: Maximum number of retry attempts.
        backoff_factor: Base factor for exponential backoff.
        max_backoff: Maximum seconds to wait between retries.
        logger_name: Name of the logger to use. Defaults to module logger.
        
    Returns:
        Callable: The wrapped function.
    """
    log = logging.getLogger(logger_name) if logger_name else logger

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt == max_retries:
                    log.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                    raise
                
                wait_time = calculate_backoff(attempt, backoff_factor, max_backoff)
                log.warning(
                    f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {wait_time:.2f} seconds..."
                )
                time.sleep(wait_time)
                
        # Should not reach here, but just in case
        raise last_exception

    return wrapper


def retry_call(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[Dict[str, Any]] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    max_backoff: float = 60.0
) -> Any:
    """
    Helper to call a function with retry logic without using the decorator.
    
    Args:
        func: The function to call.
        args: Positional arguments for the function.
        kwargs: Keyword arguments for the function.
        exceptions: Tuple of exception types to catch and retry.
        max_retries: Maximum number of retry attempts.
        backoff_factor: Base factor for exponential backoff.
        max_backoff: Maximum seconds to wait between retries.
        
    Returns:
        Any: The result of the function call.
    """
    if kwargs is None:
        kwargs = {}
        
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                raise
            
            wait_time = calculate_backoff(attempt, backoff_factor, max_backoff)
            logger.warning(
                f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                f"Retrying in {wait_time:.2f} seconds..."
            )
            time.sleep(wait_time)
            
    raise last_exception
