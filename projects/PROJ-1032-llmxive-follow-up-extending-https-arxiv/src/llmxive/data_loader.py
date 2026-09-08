"""Data loading module for GSM8K with integrity checks."""
import hashlib
import os
from typing import Generator, Dict, Any, Optional
from datasets import load_dataset
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR
import logging

logger = logging.getLogger(__name__)

def load_gsm8k_stream(
    split: str = "train",
    streaming: bool = True,
    seed: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream GSM8K dataset.
    
    Args:
        split: Dataset split ('train' or 'test').
        streaming: Whether to stream the dataset.
        seed: Random seed for reproducibility (if not streaming).
    
    Returns:
        Generator yielding dataset examples.
    
    Raises:
        DATA_INTEGRITY_ERROR: If data integrity checks fail.
    """
    try:
        if streaming:
            dataset = load_dataset("openai/gsm8k", "main", split=split, streaming=True)
        else:
            dataset = load_dataset("openai/gsm8k", "main", split=split, seed=seed)
        
        # Basic integrity check: ensure dataset is not empty
        first_item = next(iter(dataset))
        if not first_item:
            raise DATA_INTEGRITY_ERROR("Dataset stream returned empty item.")
        
        # Re-inject the first item since we consumed it
        dataset = load_dataset("openai/gsm8k", "main", split=split, streaming=streaming)
        
        return iter(dataset)
    except Exception as e:
        logger.error(f"Failed to load GSM8K dataset: {e}")
        raise DATA_INTEGRITY_ERROR(f"Data loading failed: {str(e)}") from e

def verify_no_overlap(train_indices: set, test_indices: set) -> bool:
    """
    Verify that training and test indices do not overlap.
    
    Args:
        train_indices: Set of indices used for training.
        test_indices: Set of indices used for testing.
    
    Returns:
        True if no overlap.
    
    Raises:
        DATA_INTEGRITY_ERROR: If overlap is detected.
    """
    overlap = train_indices.intersection(test_indices)
    if overlap:
        raise DATA_INTEGRITY_ERROR(
            f"Data integrity error: Found {len(overlap)} overlapping indices between "
            f"training and test sets."
        )
    return True
