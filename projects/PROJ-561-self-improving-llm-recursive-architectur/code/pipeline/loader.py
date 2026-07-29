"""
Dataset loaders for the self-improving LLM pipeline.
Implements fail-fast logic for missing data and retry logic for transient network errors.
"""
import time
import random
import os
from functools import wraps
from typing import Callable, Any, Optional, Dict, List
from datasets import load_dataset, Dataset

# Custom exception for transient errors to distinguish from missing data
class HFTransientError(Exception):
    """Raised when a transient network error occurs during dataset loading."""
    pass

def with_exponential_backoff(func: Callable) -> Callable:
    """
    Decorator implementing exponential backoff for HuggingFace API calls.
    Uses T005b configuration: initial_delay=30s, max_retries=5.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        initial_delay = 30.0
        max_retries = 5
        current_delay = initial_delay
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if this is a transient error (network, timeout, etc.)
                error_str = str(e).lower()
                is_transient = (
                    'timeout' in error_str or 
                    'connection' in error_str or 
                    'network' in error_str or 
                    'rate limit' in error_str or
                    '503' in error_str or
                    '504' in error_str
                )
                
                if not is_transient or attempt == max_retries:
                    # If not transient or max retries reached, raise immediately
                    raise
                
                # Transient error and more retries available
                wait_time = current_delay + random.uniform(0, 1.0)  # Add jitter
                print(f"Transient error in {func.__name__}: {e}. "
                      f"Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                current_delay *= 2  # Exponential backoff
        
        raise HFTransientError(f"Failed after {max_retries} retries")
    return wrapper

@with_exponential_backoff
def load_openwebtext(split: str = "train", streaming: bool = False) -> Dataset:
    """
    Load OpenWebText dataset from HuggingFace.
    
    Args:
        split: Dataset split to load (default: "train")
        streaming: If True, stream the dataset instead of loading all into memory
        
    Returns:
        Dataset object containing the OpenWebText data
        
    Raises:
        FileNotFoundError: If the dataset cannot be found or accessed
        HFTransientError: If transient network errors persist after retries
    """
    try:
        # OpenWebText is available via the 'openwebtext' dataset on HuggingFace
        dataset = load_dataset(
            "openwebtext",
            split=split,
            streaming=streaming
        )
        return dataset
    except FileNotFoundError:
        # Re-raise immediately - no synthetic fallback
        raise FileNotFoundError(
            "OpenWebText dataset not found. "
            "Ensure internet connection and HuggingFace access. "
            "No synthetic fallback is provided."
        )
    except Exception as e:
        # Let the decorator handle transient errors
        raise e

@with_exponential_backoff
def load_gsm8k(split: str = "train", streaming: bool = False) -> Dataset:
    """
    Load GSM8K (Grade School Math 8K) dataset from HuggingFace.
    
    Args:
        split: Dataset split to load (default: "train")
        streaming: If True, stream the dataset instead of loading all into memory
        
    Returns:
        Dataset object containing the GSM8K data
        
    Raises:
        FileNotFoundError: If the dataset cannot be found or accessed
        HFTransientError: If transient network errors persist after retries
    """
    try:
        # GSM8K is available via the 'gsm8k' dataset on HuggingFace
        dataset = load_dataset(
            "gsm8k",
            "main",  # The main split
            split=split,
            streaming=streaming
        )
        return dataset
    except FileNotFoundError:
        raise FileNotFoundError(
            "GSM8K dataset not found. "
            "Ensure internet connection and HuggingFace access. "
            "No synthetic fallback is provided."
        )
    except Exception as e:
        raise e

@with_exponential_backoff
def load_arc_challenge(split: str = "train", streaming: bool = False) -> Dataset:
    """
    Load ARC-Challenge dataset from HuggingFace.
    
    Args:
        split: Dataset split to load (default: "train")
        streaming: If True, stream the dataset instead of loading all into memory
        
    Returns:
        Dataset object containing the ARC-Challenge data
        
    Raises:
        FileNotFoundError: If the dataset cannot be found or accessed
        HFTransientError: If transient network errors persist after retries
    """
    try:
        # ARC Challenge is available via the 'ai2_arc' dataset on HuggingFace
        dataset = load_dataset(
            "ai2_arc",
            "ARC-Challenge",
            split=split,
            streaming=streaming
        )
        return dataset
    except FileNotFoundError:
        raise FileNotFoundError(
            "ARC-Challenge dataset not found. "
            "Ensure internet connection and HuggingFace access. "
            "No synthetic fallback is provided."
        )
    except Exception as e:
        raise e

@with_exponential_backoff
def load_wikitext2(split: str = "train", streaming: bool = False) -> Dataset:
    """
    Load Wikitext-2 dataset from HuggingFace.
    
    Args:
        split: Dataset split to load (default: "train")
        streaming: If True, stream the dataset instead of loading all into memory
        
    Returns:
        Dataset object containing the Wikitext-2 data
        
    Raises:
        FileNotFoundError: If the dataset cannot be found or accessed
        HFTransientError: If transient network errors persist after retries
    """
    try:
        # Wikitext-2 is available via the 'wikitext' dataset on HuggingFace
        dataset = load_dataset(
            "wikitext",
            "wikitext-2-raw-v1",
            split=split,
            streaming=streaming
        )
        return dataset
    except FileNotFoundError:
        raise FileNotFoundError(
            "Wikitext-2 dataset not found. "
            "Ensure internet connection and HuggingFace access. "
            "No synthetic fallback is provided."
        )
    except Exception as e:
        raise e

def load_all_datasets(streaming: bool = False) -> Dict[str, Dataset]:
    """
    Load all required datasets for the pipeline.
    
    Args:
        streaming: If True, stream datasets instead of loading all into memory
        
    Returns:
        Dictionary mapping dataset names to Dataset objects
        
    Raises:
        FileNotFoundError: If any dataset cannot be found (fail-fast)
        HFTransientError: If transient network errors persist after retries
    """
    datasets = {}
    
    datasets["openwebtext"] = load_openwebtext(streaming=streaming)
    datasets["gsm8k"] = load_gsm8k(streaming=streaming)
    datasets["arc_challenge"] = load_arc_challenge(streaming=streaming)
    datasets["wikitext2"] = load_wikitext2(streaming=streaming)
    
    return datasets
