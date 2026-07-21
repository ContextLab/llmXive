import time
import random
from functools import wraps
from typing import Callable, Any, TypeVar, Optional
from datasets import load_dataset
import os

T = TypeVar('T')

def exponential_backoff(
    initial_delay: float = 30.0,
    max_retries: int = 5,
    max_delay: float = 300.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator implementing exponential backoff with jitter for HuggingFace API calls.
    
    Parameters:
        initial_delay: Initial delay in seconds (default: 30s)
        max_retries: Maximum number of retry attempts (default: 5)
        max_delay: Maximum delay cap in seconds (default: 300s)
        exponential_base: Base for exponential calculation (default: 2.0)
        jitter: Whether to add random jitter to delay (default: True)
    
    Returns:
        Decorated function that retries on failure with exponential backoff.
    
    Raises:
        The original exception if all retries are exhausted.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        # Final attempt failed, raise the exception
                        raise e
                    
                    # Calculate delay with exponential backoff
                    sleep_time = min(delay, max_delay)
                    
                    # Add jitter if enabled
                    if jitter:
                        jitter_factor = random.uniform(0.1, 1.0)
                        sleep_time = sleep_time * jitter_factor
                    
                    print(f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}")
                    print(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    
                    # Exponentially increase delay for next attempt
                    delay *= exponential_base
            
            # Should not reach here, but just in case
            raise last_exception if last_exception else RuntimeError("Exponential backoff failed without exception")
        
        return wrapper
    return decorator

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_openwebtext() -> Any:
    """
    Load OpenWebText dataset from HuggingFace with exponential backoff.
    
    Returns:
        Loaded dataset object.
    
    Raises:
        Exception if dataset cannot be loaded after max retries.
    """
    return load_dataset("openwebtext", split="train")

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_gsm8k() -> Any:
    """
    Load GSM8K dataset from HuggingFace with exponential backoff.
    
    Returns:
        Loaded dataset object.
    
    Raises:
        Exception if dataset cannot be loaded after max retries.
    """
    return load_dataset("gsm8k", "main", split="train")

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_arc_challenge() -> Any:
    """
    Load ARC-Challenge dataset from HuggingFace with exponential backoff.
    
    Returns:
        Loaded dataset object.
    
    Raises:
        Exception if dataset cannot be loaded after max retries.
    """
    return load_dataset("ai2_arc", "ARC-Challenge", split="test")

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_wikitext2() -> Any:
    """
    Load Wikitext-2 dataset from HuggingFace with exponential backoff.
    
    Returns:
        Loaded dataset object.
    
    Raises:
        Exception if dataset cannot be loaded after max retries.
    """
    return load_dataset("wikitext", "wikitext-2-raw-v1", split="test")

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_all_datasets() -> dict:
    """
    Load all datasets with exponential backoff.
    
    Returns:
        Dictionary containing all loaded datasets.
    
    Raises:
        Exception if any dataset cannot be loaded after max retries.
    """
    return {
        "openwebtext": load_openwebtext(),
        "gsm8k": load_gsm8k(),
        "arc_challenge": load_arc_challenge(),
        "wikitext2": load_wikitext2()
    }