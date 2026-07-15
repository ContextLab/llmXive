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
    
    Args:
        initial_delay: Initial delay in seconds (default: 30s)
        max_retries: Maximum number of retry attempts (default: 5)
        max_delay: Maximum delay cap in seconds (default: 300s)
        exponential_base: Base for exponential calculation (default: 2.0)
        jitter: Whether to add random jitter to delay (default: True)
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
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
                        raise e
                    
                    # Calculate delay with exponential backoff
                    current_delay = min(delay, max_delay)
                    
                    # Add jitter if enabled
                    if jitter:
                        current_delay = current_delay * (0.5 + random.random() * 0.5)
                    
                    # Log retry attempt
                    print(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                          f"Retrying in {current_delay:.2f}s...")
                    
                    time.sleep(current_delay)
                    delay *= exponential_base
            
            # Should never reach here, but just in case
            raise last_exception
        return wrapper
    return decorator

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_openwebtext() -> Any:
    """
    Load OpenWebText dataset with exponential backoff retry logic.
    
    Returns:
        HuggingFace Dataset object
    
    Raises:
        Exception: If all retry attempts fail
    """
    return load_dataset("openwebtext", split="train", streaming=True)

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_gsm8k() -> Any:
    """
    Load GSM8K dataset with exponential backoff retry logic.
    
    Returns:
        HuggingFace Dataset object
    
    Raises:
        Exception: If all retry attempts fail
    """
    return load_dataset("gsm8k", "main", split="train", streaming=True)

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_arc_challenge() -> Any:
    """
    Load ARC-Challenge dataset with exponential backoff retry logic.
    
    Returns:
        HuggingFace Dataset object
    
    Raises:
        Exception: If all retry attempts fail
    """
    return load_dataset("ai2_arc", "ARC-Challenge", split="test", streaming=True)

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_wikitext2() -> Any:
    """
    Load Wikitext-2 dataset with exponential backoff retry logic.
    
    Returns:
        HuggingFace Dataset object
    
    Raises:
        Exception: If all retry attempts fail
    """
    return load_dataset("wikitext", "wikitext-2-raw-v1", split="test", streaming=True)

def load_all_datasets() -> dict:
    """
    Load all required datasets with fail-fast logic (no synthetic fallbacks).
    
    Returns:
        Dictionary containing all loaded datasets
    
    Raises:
        Exception: If any dataset fails to load (fail-fast behavior)
    """
    datasets = {}
    try:
        datasets['openwebtext'] = load_openwebtext()
    except Exception as e:
        raise RuntimeError(f"Failed to load OpenWebText dataset: {e}")
    
    try:
        datasets['gsm8k'] = load_gsm8k()
    except Exception as e:
        raise RuntimeError(f"Failed to load GSM8K dataset: {e}")
    
    try:
        datasets['arc_challenge'] = load_arc_challenge()
    except Exception as e:
        raise RuntimeError(f"Failed to load ARC-Challenge dataset: {e}")
    
    try:
        datasets['wikitext2'] = load_wikitext2()
    except Exception as e:
        raise RuntimeError(f"Failed to load Wikitext-2 dataset: {e}")
    
    return datasets