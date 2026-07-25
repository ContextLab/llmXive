"""
Dataset loaders for the self-improving LLM pipeline.

Implements fail-fast loading for OpenWebText, GSM8K, ARC-Challenge, and Wikitext-2.
Uses the exponential backoff wrapper for resilience against transient HuggingFace API errors.
NO synthetic fallbacks are permitted; failures must raise exceptions.
"""
import time
import random
from functools import wraps
from typing import Callable, Any, Optional, Dict, List
import os

from datasets import load_dataset

# Import the backoff wrapper from the same module (defined below)
from pipeline.loader import exponential_backoff


@exponential_backoff(initial_delay=30, max_retries=5)
def load_openwebtext() -> Any:
    """
    Load the OpenWebText dataset from HuggingFace.
    
    Returns:
        DatasetDict or Dataset containing the OpenWebText data.
        
    Raises:
      Exception: If the dataset cannot be loaded after retries.
    """
    # OpenWebText is often accessed via the 'openwebtext' repo on HF
    # Note: This dataset may require authentication or be behind a gate in some contexts.
    # We attempt the standard load.
    try:
        ds = load_dataset("openwebtext", split="train", streaming=False)
        return ds
    except Exception as e:
        # Re-raise to trigger backoff or final failure
        raise e


@exponential_backoff(initial_delay=30, max_retries=5)
def load_gsm8k() -> Any:
    """
    Load the GSM8K (Grade School Math) dataset.
    
    Returns:
        DatasetDict or Dataset containing the GSM8K data.
        
    Raises:
      Exception: If the dataset cannot be loaded after retries.
    """
    try:
        ds = load_dataset("gsm8k", "main", split="train", streaming=False)
        return ds
    except Exception as e:
        raise e


@exponential_backoff(initial_delay=30, max_retries=5)
def load_arc_challenge() -> Any:
    """
    Load the ARC-Challenge dataset.
    
    Returns:
        DatasetDict or Dataset containing the ARC-Challenge data.
        
    Raises:
      Exception: If the dataset cannot be loaded after retries.
    """
    try:
        ds = load_dataset("ai2_arc", "ARC-Challenge", split="train", streaming=False)
        return ds
    except Exception as e:
        raise e


@exponential_backoff(initial_delay=30, max_retries=5)
def load_wikitext2() -> Any:
    """
    Load the Wikitext-2 dataset.
    
    Returns:
        DatasetDict or Dataset containing the Wikitext-2 data.
        
    Raises:
      Exception: If the dataset cannot be loaded after retries.
    """
    try:
        ds = load_dataset("wikitext", "wikitext-2-raw-v1", split="train", streaming=False)
        return ds
    except Exception as e:
        raise e


def load_all_datasets() -> Dict[str, Any]:
    """
    Load all required datasets and return them in a dictionary.
    
    This function enforces the fail-fast policy: if any single dataset
    fails to load, the entire operation raises an exception and no
    synthetic data is generated.
    
    Returns:
        Dict mapping dataset name to loaded dataset object.
        
    Raises:
      Exception: If any dataset fails to load.
    """
    datasets = {}
    
    try:
        datasets['openwebtext'] = load_openwebtext()
    except Exception as e:
        raise RuntimeError(f"Failed to load OpenWebText: {e}")
        
    try:
        datasets['gsm8k'] = load_gsm8k()
    except Exception as e:
        raise RuntimeError(f"Failed to load GSM8K: {e}")
        
    try:
        datasets['arc_challenge'] = load_arc_challenge()
    except Exception as e:
        raise RuntimeError(f"Failed to load ARC-Challenge: {e}")
        
    try:
        datasets['wikitext2'] = load_wikitext2()
    except Exception as e:
        raise RuntimeError(f"Failed to load Wikitext-2: {e}")
        
    return datasets
