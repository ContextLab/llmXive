import os
import sys
import logging
from typing import Dict, Any, Iterator, Optional, List, Tuple
from pathlib import Path
from utils.logging import get_logger, error, info, warning

logger = get_logger(__name__)

class DataLoaderError(Exception):
    """Custom exception for data loading errors."""
    pass

def validate_streaming_source(source: str) -> bool:
    """
    Validate that a streaming source is reachable.
    
    Args:
        source: The dataset source identifier (e.g., "tinyimagenet", "c4")
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        DataLoaderError: If the source is not reachable
    """
    # In a real implementation, this would attempt to connect or fetch metadata
    # For now, we validate against known sources
    known_sources = {"tinyimagenet", "c4", "wikitext"}
    if source not in known_sources:
        raise DataLoaderError(f"Unknown streaming source: {source}")
    
    # Simulate a check - in reality, this would hit the HuggingFace API
    info(f"Validating streaming source: {source}")
    return True

def load_tinyimagenet_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load TinyImageNet dataset in streaming mode.
    
    Yields:
        Dict containing 'image', 'label', and metadata
    """
    validate_streaming_source("tinyimagenet")
    
    try:
        from datasets import load_dataset
        # Stream the dataset
        dataset = load_dataset("tiny-imagenet-200", split="train", streaming=True)
        for item in dataset:
            yield item
    except Exception as e:
        error(f"Failed to load TinyImageNet streaming: {e}")
        # Fail loudly - do not return synthetic data
        raise DataLoaderError(f"Real data source unreachable: {e}")

def load_c4_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load C4 dataset in streaming mode.
    
    Yields:
        Dict containing 'text' and metadata
    """
    validate_streaming_source("c4")
    
    try:
        from datasets import load_dataset
        dataset = load_dataset("allenai/c4", "en", split="train", streaming=True)
        for item in dataset:
            yield item
    except Exception as e:
        error(f"Failed to load C4 streaming: {e}")
        raise DataLoaderError(f"Real data source unreachable: {e}")

def get_sample_iterator(source: str, max_samples: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """
    Get an iterator over samples from a specified source.
    
    Args:
        source: Dataset source name
        max_samples: Optional limit on number of samples
        
    Returns:
        Iterator yielding samples
    """
    if source == "tinyimagenet":
        iterator = load_tinyimagenet_streaming()
    elif source == "c4":
        iterator = load_c4_streaming()
    else:
        raise DataLoaderError(f"Unsupported source: {source}")
    
    if max_samples:
        from itertools import islice
        return islice(iterator, max_samples)
    
    return iterator

def main():
    """Test the data loader."""
    try:
        info("Testing TinyImageNet streaming loader...")
        count = 0
        for sample in get_sample_iterator("tinyimagenet", max_samples=5):
            count += 1
            info(f"Sample {count}: {sample.keys()}")
        info(f"Successfully loaded {count} samples.")
    except DataLoaderError as e:
        error(f"Data loader failed as expected for missing source: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
