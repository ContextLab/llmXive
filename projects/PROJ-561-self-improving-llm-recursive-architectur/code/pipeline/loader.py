import time
import random
from functools import wraps
from typing import Callable, Any, Optional, Dict, List
import os

from pipeline.loader import exponential_backoff

# Re-export the backoff decorator defined in this file below
__all__ = [
    "exponential_backoff",
    "load_openwebtext",
    "load_gsm8k",
    "load_arc_challenge",
    "load_wikitext2",
    "load_all_datasets"
]

T = TypeVar("T")

def exponential_backoff(
    initial_delay: float = 30.0,
    max_retries: int = 5,
    max_delay: float = 300.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator implementing exponential backoff with jitter for API calls.
    
    Args:
        initial_delay: Initial delay in seconds (default 30s per T005b).
        max_retries: Maximum number of retry attempts (default 5).
        max_delay: Maximum delay cap in seconds.
    
    Returns:
        Decorated function with retry logic.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 to include initial attempt
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise e
                    
                    # Exponential backoff with jitter
                    jitter = random.uniform(0.1, 0.5)
                    sleep_time = min(delay + jitter, max_delay)
                    print(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    delay *= 2
            
            # Should not reach here, but safe fallback
            raise last_exception
        return wrapper
    return decorator

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_openwebtext(split: str = "train", streaming: bool = True) -> Any:
    """
    Loads the OpenWebText dataset from HuggingFace.
    
    Args:
        split: Dataset split to load (default 'train').
        streaming: If True, streams the dataset without downloading fully.
    
    Returns:
        HuggingFace Dataset object.
    
    Raises:
        Exception: If the dataset cannot be loaded after retries (Fail-Fast).
    """
    # Using the 'openwebtext' dataset which is the standard open-source
    # equivalent often used in research. 
    # Note: The original OpenWebText is not directly on HF, but 'openwebtext' 
    # from the community or 'stas/openwebtext-10k' are common proxies.
    # We use 'stas/openwebtext-10k' as a verified small subset if full is too large,
    # OR the standard 'openwebtext' if available. 
    # To ensure real data and fail-fast, we attempt the primary source.
    dataset = load_dataset("openwebtext", split=split, streaming=streaming)
    return dataset

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_gsm8k(split: str = "train", streaming: bool = True) -> Any:
    """
    Loads the GSM8K (Grade School Math) dataset.
    
    Args:
        split: Dataset split to load (default 'train').
        streaming: If True, streams the dataset.
    
    Returns:
        HuggingFace Dataset object.
    """
    dataset = load_dataset("gsm8k", "main", split=split, streaming=streaming)
    return dataset

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_arc_challenge(split: str = "train", streaming: bool = True) -> Any:
    """
    Loads the ARC-Challenge dataset.
    
    Args:
        split: Dataset split to load (default 'train').
        streaming: If True, streams the dataset.
    
    Returns:
        HuggingFace Dataset object.
    """
    # ARC has 'challenge' and 'easy' subsets. We load 'challenge'.
    dataset = load_dataset("ai2_arc", "ARC-Challenge", split=split, streaming=streaming)
    return dataset

@exponential_backoff(initial_delay=30.0, max_retries=5)
def load_wikitext2(split: str = "train", streaming: bool = True) -> Any:
    """
    Loads the Wikitext-2 dataset.
    
    Args:
        split: Dataset split to load (default 'train').
        streaming: If True, streams the dataset.
    
    Returns:
        HuggingFace Dataset object.
    """
    dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split=split, streaming=streaming)
    return dataset

def load_all_datasets(streaming: bool = True) -> dict:
    """
    Loads all required datasets for the pipeline.
    
    Args:
        streaming: Whether to stream datasets.
    
    Returns:
        Dictionary mapping dataset names to dataset objects.
    
    Raises:
        Exception: If any dataset fails to load (Fail-Fast).
    """
    datasets = {}
    try:
        datasets["openwebtext"] = load_openwebtext(streaming=streaming)
        datasets["gsm8k"] = load_gsm8k(streaming=streaming)
        datasets["arc_challenge"] = load_arc_challenge(streaming=streaming)
        datasets["wikitext2"] = load_wikitext2(streaming=streaming)
    except Exception as e:
        # Fail-Fast: Re-raise immediately if any load fails.
        # No synthetic fallback allowed.
        raise RuntimeError(f"Failed to load one or more datasets: {e}")
    
    return datasets
