import time
import random
from functools import wraps
from typing import Callable, Any, Optional, Dict, List
import os
from datasets import load_dataset

def exponential_backoff(
    initial_delay: float = 30.0,
    max_retries: int = 5,
    max_delay: float = 300.0,
    backoff_factor: float = 2.0
) -> Callable:
    """
    Decorator that wraps a function to implement exponential backoff retry logic.
    
    Specifically designed for HuggingFace API calls which may experience rate limiting
    or transient network errors.
    
    Args:
        initial_delay: Initial delay in seconds before the first retry (default: 30s)
        max_retries: Maximum number of retry attempts (default: 5)
        max_delay: Maximum delay between retries in seconds (default: 300s / 5min)
        backoff_factor: Factor by which delay increases each retry (default: 2.0)
    
    Returns:
        Decorated function with retry logic
    
    Raises:
        The original exception if all retries are exhausted
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 to include initial attempt
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        # All retries exhausted
                        raise e
                    
                    # Calculate next delay with exponential backoff
                    delay = min(delay * backoff_factor, max_delay)
                    # Add jitter to prevent thundering herd
                    jitter = random.uniform(0.1, 0.5) * delay
                    actual_delay = delay + jitter
                    
                    print(f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}")
                    print(f"Retrying in {actual_delay:.2f} seconds...")
                    time.sleep(actual_delay)
                    # Reset delay for next iteration (it will be multiplied by backoff_factor)
                    delay = delay / backoff_factor
            
            # Should never reach here, but just in case
            raise last_exception
        return wrapper
    return decorator

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_openwebtext() -> Any:
    """
    Load OpenWebText dataset from HuggingFace with exponential backoff.
    
    Returns:
        Loaded dataset object
    """
    return load_dataset("openwebtext", split="train")

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_gsm8k() -> Any:
    """
    Load GSM8K dataset from HuggingFace with exponential backoff.
    
    Returns:
        Loaded dataset object
    """
    return load_dataset("gsm8k", "main", split="train")

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_arc_challenge() -> Any:
    """
    Load ARC-Challenge dataset from HuggingFace with exponential backoff.
    
    Returns:
        Loaded dataset object
    """
    return load_dataset("ai2_arc", "ARC-Challenge", split="validation")

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_wikitext2() -> Any:
    """
    Load Wikitext-2 dataset from HuggingFace with exponential backoff.
    
    Returns:
        Loaded dataset object
    """
    return load_dataset("wikitext", "wikitext-2-raw-v1", split="train")

def load_all_datasets() -> Dict[str, Any]:
    """
    Load all required datasets with exponential backoff protection.
    
    Returns:
        Dictionary containing all loaded datasets
    """
    return {
        "openwebtext": load_openwebtext(),
        "gsm8k": load_gsm8k(),
        "arc_challenge": load_arc_challenge(),
        "wikitext2": load_wikitext2()
    }