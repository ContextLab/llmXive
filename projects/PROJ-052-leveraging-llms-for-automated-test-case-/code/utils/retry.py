"""
Shared retry logic for the llmXive pipeline.
Extracted from test_executor.py and llm_generator.py to remove duplication.
"""
import logging
import time
from typing import Callable, TypeVar, Optional, Any
from config import get_timeout_compile, get_timeout_inference

T = TypeVar('T')

logger = logging.getLogger(__name__)

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    timeout: Optional[float] = None,
    exception_types: tuple = (Exception,)
) -> Callable[..., T]:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        func: The function to wrap.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds between retries.
        timeout: Optional global timeout for the entire operation.
        exception_types: Tuple of exception types to catch and retry.
        
    Returns:
        The wrapped function.
        
    Raises:
        The last exception raised if all retries fail.
    """
    def wrapper(*args, **kwargs) -> T:
        last_exception = None
        start_time = time.time()
        
        for attempt in range(1, max_retries + 1):
            try:
                # Check global timeout if set
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed > timeout:
                        raise TimeoutError(f"Operation timed out after {elapsed:.2f}s")
                
                result = func(*args, **kwargs)
                if attempt > 1:
                    logger.info(f"Function {func.__name__} succeeded on attempt {attempt}")
                return result
                
            except exception_types as e:
                last_exception = e
                if attempt == max_retries:
                    logger.error(f"Function {func.__name__} failed after {max_retries} attempts: {e}")
                    raise
                
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(f"Attempt {attempt} failed for {func.__name__}: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
                
        raise last_exception  # type: ignore
        
    return wrapper

def execute_with_retry(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    timeout: Optional[float] = None,
    exception_types: tuple = (Exception,)
) -> T:
    """
    Execute a function with retry logic (non-decorator version).
    
    Args:
        func: The function to execute.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds between retries.
        timeout: Optional global timeout for the entire operation.
        exception_types: Tuple of exception types to catch and retry.
        
    Returns:
        The result of the function.
        
    Raises:
        The last exception raised if all retries fail.
    """
    last_exception = None
    start_time = time.time()
    
    for attempt in range(1, max_retries + 1):
        try:
            # Check global timeout if set
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise TimeoutError(f"Operation timed out after {elapsed:.2f}s")
            
            result = func()
            if attempt > 1:
                logger.info(f"Operation succeeded on attempt {attempt}")
            return result
            
        except exception_types as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(f"Operation failed after {max_retries} attempts: {e}")
                raise
            
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.1f}s...")
            time.sleep(delay)
            
    raise last_exception  # type: ignore
