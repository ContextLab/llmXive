import time
import os
import logging
from functools import wraps
from typing import Callable, Any, Optional, Dict, List, Union
from datasets import load_dataset, Dataset

logger = logging.getLogger(__name__)

class HFTransientError(Exception):
    """Exception raised for transient HuggingFace API errors."""
    pass

def exponential_backoff_retry(max_retries: int = 5, initial_delay: float = 30.0):
    """
    Decorator implementing exponential backoff for transient network errors.
    Distinct from fail-fast logic: only catches transient errors, not missing files.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError, HFTransientError) as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise
                    logger.warning(f"Transient error in {func.__name__}, attempt {attempt + 1}/{max_retries + 1}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    delay *= 2
                except FileNotFoundError as e:
                    # Fail-fast: missing files are NOT transient, re-raise immediately
                    logger.error(f"File not found (fail-fast): {e}")
                    raise
            raise last_exception
        return wrapper
    return decorator

@exponential_backoff_retry(max_retries=5, initial_delay=30.0)
def load_openwebtext(split: str = "train", streaming: bool = False) -> Dataset:
    """Load OpenWebText dataset from HuggingFace."""
    path = "openwebtext"
    if not os.path.exists(path) and not streaming:
        # Fail-fast check for local file existence if not streaming
        if not os.path.exists(path):
            raise FileNotFoundError(f"Dataset file not found: {path}")
    return load_dataset(path, split=split, streaming=streaming)

@exponential_backoff_retry(max_retries=5, initial_delay=30.0)
def load_gsm8k(split: str = "test", streaming: bool = False) -> Dataset:
    """Load GSM8K dataset from HuggingFace."""
    path = "gsm8k"
    if not os.path.exists(path) and not streaming:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Dataset file not found: {path}")
    return load_dataset(path, split=split, streaming=streaming)

@exponential_backoff_retry(max_retries=5, initial_delay=30.0)
def load_arc_challenge(split: str = "test", streaming: bool = False) -> Dataset:
    """Load ARC-Challenge dataset from HuggingFace."""
    path = "ai2_arc"
    if not os.path.exists(path) and not streaming:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Dataset file not found: {path}")
    return load_dataset(path, name="ARC-Challenge", split=split, streaming=streaming)

@exponential_backoff_retry(max_retries=5, initial_delay=30.0)
def load_boolq(split: str = "validation", streaming: bool = False) -> Dataset:
    """Load BoolQ dataset from HuggingFace."""
    path = "boolq"
    if not os.path.exists(path) and not streaming:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Dataset file not found: {path}")
    return load_dataset(path, split=split, streaming=streaming)

@exponential_backoff_retry(max_retries=5, initial_delay=30.0)
def load_wikitext2(split: str = "test", streaming: bool = False) -> Dataset:
    """Load WikiText-2 dataset from HuggingFace."""
    path = "wikitext"
    if not os.path.exists(path) and not streaming:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Dataset file not found: {path}")
    return load_dataset(path, "wikitext-2-raw-v1", split=split, streaming=streaming)

def load_local_dataset(path: str) -> Dataset:
    """
    Load a local dataset file. Implements fail-fast logic: raises FileNotFoundError
    immediately if the file does not exist, with NO retry logic and NO synthetic fallback.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found: {path}")
    # Assume JSON/CSV format for local loading, extend as needed
    if path.endswith('.json'):
        return load_dataset('json', data_files=path)
    elif path.endswith('.csv'):
        return load_dataset('csv', data_files=path)
    else:
        raise ValueError(f"Unsupported local dataset format: {path}")

def load_all_datasets(streaming: bool = False) -> Dict[str, Dataset]:
    """
    Load all required datasets. Uses fail-fast for missing data and backoff for network issues.
    """
    datasets = {}
    try:
        datasets['openwebtext'] = load_openwebtext(streaming=streaming)
    except FileNotFoundError as e:
        logger.critical(f"Missing training data: {e}")
        raise
    
    try:
        datasets['gsm8k'] = load_gsm8k(streaming=streaming)
    except FileNotFoundError as e:
        logger.warning(f"Missing test data (GSM8K): {e}")
        # Optional: continue if test data is missing, but fail-fast is preferred per spec
        # raise 
    
    try:
        datasets['arc'] = load_arc_challenge(streaming=streaming)
    except FileNotFoundError as e:
        logger.warning(f"Missing test data (ARC): {e}")
        # raise

    try:
        datasets['boolq'] = load_boolq(streaming=streaming)
    except FileNotFoundError as e:
        logger.warning(f"Missing test data (BoolQ): {e}")
        # raise

    return datasets
