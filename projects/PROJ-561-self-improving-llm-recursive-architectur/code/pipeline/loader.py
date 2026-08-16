import time
import os
import logging
from functools import wraps
from typing import Callable, Any, Optional, Dict, List
import torch
from datasets import load_dataset
from huggingface_hub import HfHubHTTPError
import tempfile

from config import get_config
from pipeline.loader import exponential_backoff_retry

# Re-export the retry decorator defined in this file to satisfy the API surface
# The task requires calling `exponential_backoff` from T005b.
# We define the decorator here and ensure it is imported by the API surface.
from functools import wraps

logger = logging.getLogger(__name__)

# Custom exception for transient HuggingFace errors
class HFTransientError(Exception):
    """Raised when a transient network error (429/5xx) occurs during dataset loading."""
    pass

def exponential_backoff_retry(func: Callable) -> Callable:
    """
    Decorator implementing exponential backoff for transient HuggingFace errors.
    Initial delay: 30s (±1s), Max retries: 5.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 5
        base_delay = 30.0  # 30 seconds
        attempts = 0
        
        while attempts <= max_retries:
            try:
                return func(*args, **kwargs)
            except (HfHubHTTPError, ConnectionError, TimeoutError) as e:
                # Check if it's a transient error (429 or 5xx)
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    if status_code in [429] or (500 <= status_code < 600):
                        attempts += 1
                        if attempts > max_retries:
                            logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                            raise HFTransientError(f"Failed after {max_retries} retries: {str(e)}")
                        
                        # Calculate delay with jitter: base_delay * 2^(attempts-1) + random(0, 1)
                        delay = base_delay * (2 ** (attempts - 1))
                        jitter = (time.time() % 1.0) - 0.5 # Simple jitter within ±0.5s
                        actual_delay = delay + jitter
                        
                        logger.warning(f"Transient error in {func.__name__}: {str(e)}. Retrying in {actual_delay:.2f}s (attempt {attempts}/{max_retries})")
                        time.sleep(actual_delay)
                        continue
                # If it's not a transient error, re-raise immediately
                raise

    return wrapper

@exponential_backoff_retry
def load_openwebtext() -> Any:
    """
    Loads the OpenWebText dataset from HuggingFace.
    Returns the dataset object.
    """
    logger.info("Loading OpenWebText dataset...")
    # Using streaming to handle large datasets without full download
    ds = load_dataset("openwebtext", split="train", streaming=True)
    return ds

@exponential_backoff_retry
def load_gsm8k() -> Any:
    """
    Loads the GSM8K dataset from HuggingFace.
    Returns the dataset object.
    """
    logger.info("Loading GSM8K dataset...")
    ds = load_dataset("gsm8k", "main", split="test", streaming=True)
    return ds

@exponential_backoff_retry
def load_arc_challenge() -> Any:
    """
    Loads the ARC-Challenge dataset from HuggingFace.
    Returns the dataset object.
    """
    logger.info("Loading ARC-Challenge dataset...")
    ds = load_dataset("ai2_arc", "ARC-Challenge", split="test", streaming=True)
    return ds

@exponential_backoff_retry
def load_boolq() -> Any:
    """
    Loads the BoolQ dataset from HuggingFace.
    Returns the dataset object.
    """
    logger.info("Loading BoolQ dataset...")
    ds = load_dataset("boolq", split="validation", streaming=True)
    return ds

def load_local_dataset(path: str) -> Any:
    """
    Loads a dataset from a local file path.
    Raises FileNotFoundError immediately if the file does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found: {path}")
    
    logger.info(f"Loading local dataset from {path}...")
    # Attempt to infer format or default to json/csv if extension matches
    # For robustness, we try json first, then csv
    if path.endswith('.json'):
        return load_dataset("json", data_files=path)
    elif path.endswith('.csv'):
        return load_dataset("csv", data_files=path)
    else:
        # Fallback: try to load as generic parquet or json if extension is ambiguous
        # This assumes the dataset library can handle it or raises a clear error
        return load_dataset(path) # type: ignore

def load_all_datasets() -> Dict[str, Any]:
    """
    Loads all required datasets: OpenWebText (train), GSM8K, ARC-Challenge, BoolQ (test).
    Returns a dictionary mapping dataset names to their objects.
    """
    config = get_config()
    datasets = {}
    
    # Check for local overrides in config if paths are defined
    # Assuming config.py might have paths, but the task specifies "paths defined in config.py"
    # If config has specific paths, use load_local_dataset. Otherwise, use HF loaders.
    
    # OpenWebText (Training)
    if hasattr(config, 'openwebtext_path') and config.openwebtext_path:
        datasets['openwebtext'] = load_local_dataset(config.openwebtext_path)
    else:
        datasets['openwebtext'] = load_openwebtext()
    
    # GSM8K (Test)
    if hasattr(config, 'gsm8k_path') and config.gsm8k_path:
        datasets['gsm8k'] = load_local_dataset(config.gsm8k_path)
    else:
        datasets['gsm8k'] = load_gsm8k()
        
    # ARC-Challenge (Test)
    if hasattr(config, 'arc_challenge_path') and config.arc_challenge_path:
        datasets['arc_challenge'] = load_local_dataset(config.arc_challenge_path)
    else:
        datasets['arc_challenge'] = load_arc_challenge()
        
    # BoolQ (Test)
    if hasattr(config, 'boolq_path') and config.boolq_path:
        datasets['boolq'] = load_local_dataset(config.boolq_path)
    else:
        datasets['boolq'] = load_boolq()
        
    return datasets
