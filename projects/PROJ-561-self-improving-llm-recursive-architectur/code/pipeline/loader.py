import time
import os
import logging
from functools import wraps
from typing import Callable, Any, Optional, Dict, List
import torch
from datasets import load_dataset

from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HFTransientError(Exception):
    """Exception raised for transient HuggingFace API/network errors."""
    pass

def exponential_backoff_retry(max_retries: int = 5, initial_delay: float = 30.0):
    """
    Decorator implementing exponential backoff for transient errors.
    Initial delay: 30s (±1s), Max retries: 5.
    Uses T005b logic.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 5
        initial_delay = 30.0
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (HFTransientError, ConnectionError, TimeoutError, OSError) as e:
                if attempt == max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}.")
                    raise
                
                # Calculate delay with jitter: initial_delay + random(-1, 1)
                jitter = random.uniform(-1.0, 1.0)
                delay = initial_delay + jitter
                # Ensure delay is positive
                delay = max(0.0, delay)
                
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}. "
                               f"Retrying in {delay:.2f}s due to: {e}")
                time.sleep(delay)
                
        raise RuntimeError(f"Unexpected flow in backoff for {func.__name__}")

@with_exponential_backoff
def load_openwebtext() -> Any:
    """
    Load OpenWebText dataset for training.
    Uses the 'openwebtext' dataset from HuggingFace.
    """
    logger.info("Loading OpenWebText dataset...")
    # Using streaming to avoid loading full ~40GB into memory immediately
    # The task requires real data; this fetches from the real HF source.
    dataset = load_dataset("openwebtext", split="train", streaming=True)
    return dataset

@with_exponential_backoff
def load_gsm8k() -> Any:
    """
    Load GSM8K dataset for testing.
    """
    logger.info("Loading GSM8K dataset...")
    dataset = load_dataset("gsm8k", "main", split="test", streaming=True)
    return dataset

@with_exponential_backoff
def load_arc_challenge() -> Any:
    """
    Load ARC-Challenge dataset for testing.
    """
    logger.info("Loading ARC-Challenge dataset...")
    dataset = load_dataset("ai2_arc", "ARC-Challenge", split="test", streaming=True)
    return dataset

@with_exponential_backoff
def load_boolq() -> Any:
    """
    Load BoolQ dataset for testing.
    """
    logger.info("Loading BoolQ dataset...")
    dataset = load_dataset("boolq", split="validation", streaming=True)
    return dataset

@with_exponential_backoff
def load_wikitext2() -> Any:
    """
    Load WikiText-2 dataset (often used for perplexity evaluation).
    """
    logger.info("Loading WikiText-2 dataset...")
    dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="test", streaming=True)
    return dataset

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
    Load a dataset from a local file path.
    
    Args:
        path: Path to the dataset file or directory.
        
    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the file format is unsupported.
        
    Logic:
        - Checks existence immediately.
        - Raises FileNotFoundError with exact message "Dataset file not found: {path}"
        - No synthetic fallback.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found: {path}")
    
    logger.info(f"Loading local dataset from {path}...")
    
    # Infer format based on extension or load as generic dataset
    # Assuming HuggingFace datasets format or common CSV/JSON
    try:
        if path.endswith('.parquet') or path.endswith('.csv') or path.endswith('.json'):
            # Generic load attempt, relies on datasets library inference
            dataset = load_dataset("csv" if path.endswith('.csv') else "json" if path.endswith('.json') else "parquet", data_files=path, split="train")
        else:
            # Try loading as a directory of dataset files
            dataset = load_dataset(path, split="train")
    except Exception as e:
        logger.error(f"Failed to load local dataset from {path}: {e}")
        raise

    return dataset

def load_all_datasets(streaming: bool = False) -> Dict[str, Dataset]:
    """
    Convenience function to load all required datasets.
    Returns a dictionary with keys: 'train', 'gsm8k', 'arc', 'boolq'.
    """
    config = get_config()
    datasets = {}
    
    # Training data
    datasets['train'] = load_openwebtext()
    
    # Test data
    datasets['gsm8k'] = load_gsm8k()
    datasets['arc'] = load_arc_challenge()
    datasets['boolq'] = load_boolq()
    
    return datasets
