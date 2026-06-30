"""
Utility functions with enhanced error handling and retry logic.
"""
import time
import random
from typing import Callable, TypeVar, Optional, Any, Tuple
from functools import wraps
import logging

from error_handling import api_logger, log_error

T = TypeVar('T')

def exponential_backoff_retry(max_retries: int = 3, base_delay: float = 1.0, 
                             max_delay: float = 60.0, jitter: bool = True):
    """
    Decorator for functions that need exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter to delays
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            task_id = kwargs.get('task_id') or args[0] if args else "unknown"
            
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (TimeoutError, ConnectionError, RuntimeError) as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Check if it's a retryable error
                    is_retryable = any(keyword in error_msg for keyword in 
                                     ["rate limit", "429", "too many requests", 
                                      "connection", "timeout", "temporary"])
                    
                    if not is_retryable or attempt == max_retries:
                        api_logger.error(f"[{task_id}] Non-retryable error or max retries reached: {e}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    api_logger.warning(
                        f"[{task_id}] Attempt {attempt}/{max_retries} failed. "
                        f"Retrying in {delay:.2f}s: {e}"
                    )
                    time.sleep(delay)
                
                except Exception as e:
                    # Non-retryable exception
                    api_logger.error(f"[{task_id}] Unexpected error: {e}")
                    raise
            
            # Should not reach here, but just in case
            raise last_exception or RuntimeError("Retry logic failed")
        
        return wrapper
    return decorator

def retry_with_backoff(func: Callable, max_retries: int = 3, base_delay: float = 1.0,
                      max_delay: float = 60.0, task_id: Optional[str] = None):
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        task_id: Task identifier for logging
    
    Returns:
        Result of the function
    
    Raises:
        Last exception if all retries fail
    """
    task_id = task_id or "unknown"
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except (TimeoutError, ConnectionError, RuntimeError) as e:
            last_exception = e
            error_msg = str(e).lower()
            
            is_retryable = any(keyword in error_msg for keyword in 
                             ["rate limit", "429", "too many requests", 
                              "connection", "timeout", "temporary"])
            
            if not is_retryable or attempt == max_retries:
                api_logger.error(f"[{task_id}] Non-retryable error or max retries reached: {e}")
                raise
            
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            delay = delay * (0.5 + random.random())  # Add jitter
            
            api_logger.warning(
                f"[{task_id}] Attempt {attempt}/{max_retries} failed. "
                f"Retrying in {delay:.2f}s: {e}"
            )
            time.sleep(delay)
    
    raise last_exception or RuntimeError("Retry logic failed")

def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary, handling nested keys.
    
    Args:
        dictionary: Source dictionary
        key: Key to retrieve (supports dot notation for nested access)
        default: Default value if key not found
    
    Returns:
        Value or default
    """
    if not isinstance(dictionary, dict):
        return default
    
    keys = key.split('.') if '.' in key else [key]
    current = dictionary
    
    try:
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current
    except (KeyError, TypeError, AttributeError):
        return default

def format_bytes(size: int) -> str:
    """
    Format bytes into human-readable string.
    
    Args:
        size: Size in bytes
    
    Returns:
        Human-readable string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

# Re-export for compatibility
__all__ = [
    'exponential_backoff_retry',
    'retry_with_backoff', 
    'safe_get',
    'format_bytes'
]