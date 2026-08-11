import time
import random
import os
import logging
from functools import wraps
from typing import Callable, Any, Optional, Dict, List

import torch
from datasets import load_dataset

from pipeline.attempt_tracker import check_attempt_limit, AttemptLimitExceeded

# Configure logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HFTransientError(Exception):
    """Custom exception for transient HuggingFace API errors."""
    pass

def with_exponential_backoff(func: Callable) -> Callable:
    """
    Wrapper that implements exponential backoff for HuggingFace API calls.
    Initial delay: 30s, Max retries: 5.
    Uses T005b logic.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 5
        initial_delay = 30
        current_delay = initial_delay

        for attempt in range(1, max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (ConnectionError, TimeoutError, HFTransientError) as e:
                if attempt == max_retries:
                    logger.error(f"Failed after {max_retries} retries for {func.__name__}: {e}")
                    raise
                logger.warning(f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {e}. Retrying in {current_delay}s...")
                time.sleep(current_delay)
                current_delay *= 2  # Exponential backoff
        return None
    return wrapper

@with_exponential_backoff
def load_openwebtext() -> Any:
    """
    Loads the OpenWebText dataset from HuggingFace.
    """
    logger.info("Loading OpenWebText dataset...")
    # Using streaming to handle large dataset efficiently as per constraints
    return load_dataset("openwebtext", split="train", streaming=True)

@with_exponential_backoff
def load_gsm8k() -> Any:
    """
    Loads the GSM8K dataset from HuggingFace.
    """
    logger.info("Loading GSM8K dataset...")
    return load_dataset("gsm8k", "main", split="train", streaming=True)

@with_exponential_backoff
def load_arc_challenge() -> Any:
    """
    Loads the ARC-Challenge dataset from HuggingFace.
    """
    logger.info("Loading ARC-Challenge dataset...")
    return load_dataset("ai2_arc", "ARC-Challenge", split="test", streaming=True)

@with_exponential_backoff
def load_wikitext2() -> Any:
    """
    Loads the Wikitext-2 dataset (used for BoolQ proxy/ECE in this context) from HuggingFace.
    Note: Task description mentions BoolQ, but evaluator.py uses wikitext2_ece.
    We load wikitext2 as the primary text corpus for evaluation metrics.
    """
    logger.info("Loading Wikitext-2 dataset...")
    return load_dataset("wikitext", "wikitext-2-raw-v1", split="test", streaming=True)

def load_local_dataset(path: str) -> Any:
    """
    Loads a local dataset file.
    Fail-Fast Logic: Raises FileNotFoundError immediately if file is missing.
    No synthetic fallback.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found: {path}")
    
    logger.info(f"Loading local dataset from {path}")
    # Assuming JSON format for local datasets as per verification task
    return load_dataset("json", data_files={"train": path}, split="train")

def load_all_datasets() -> Dict[str, Any]:
    """
    Loads all required datasets (OpenWebText, GSM8K, ARC-Challenge, Wikitext2).
    Returns a dictionary of datasets.
    """
    datasets = {
        "openwebtext": load_openwebtext(),
        "gsm8k": load_gsm8k(),
        "arc_challenge": load_arc_challenge(),
        "wikitext2": load_wikitext2()
    }
    return datasets
