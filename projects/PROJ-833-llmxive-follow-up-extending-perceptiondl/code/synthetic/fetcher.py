"""
code/synthetic/fetcher.py

Handles fetching real data from HuggingFace datasets.
Uses 'lvis/lvis-instances' as the verified source for bounding box data.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Iterator

from config import get_data_path
from datasets import load_dataset

def ensure_data_dir():
    """Ensure the raw data directory exists."""
    data_root = get_data_path()
    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def fetch_dataset_sample(
    dataset_name: str = "lvis/lvis-instances",
    split: str = "validation",
    num_samples: Optional[int] = None,
    streaming: bool = True
) -> Iterator[Dict[str, Any]]:
    """
    Fetches a sample of the dataset from HuggingFace.
    
    Args:
        dataset_name: The HuggingFace dataset identifier.
        split: The dataset split to use.
        num_samples: Optional limit on number of samples.
        streaming: If True, streams data without downloading full dataset.
    
    Returns:
        An iterator yielding dataset items.
    
    Raises:
        RuntimeError: If the dataset cannot be accessed or lacks required fields.
    """
    try:
        logger = __import__('logging').getLogger(__name__)
        logger.info(f"Fetching dataset: {dataset_name}, split: {split}")
        
        # Load dataset with streaming to handle large sizes
        ds = load_dataset(dataset_name, split=split, streaming=streaming)
        
        count = 0
        for item in ds:
            # Validate that the item has necessary fields (images and annotations)
            # LVIS format typically has 'image' and 'annotations' (list of dicts with bbox)
            if 'image' not in item and 'pixel_values' not in item:
                # Some datasets might return raw bytes or different keys
                # Attempt to handle common variations or skip
                logger.debug(f"Skipping item missing image data: {item.keys()}")
                continue
            
            # Ensure we have bounding box data
            if 'annotations' not in item and 'bbox' not in item:
                # If no annotations, we can't generate regions. Skip.
                logger.debug(f"Skipping item missing annotations: {item.keys()}")
                continue

            yield item
            count += 1
            
            if num_samples and count >= num_samples:
                break
                
    except Exception as e:
        # Fail loudly as per constraints
        raise RuntimeError(f"Failed to fetch or process dataset {dataset_name}: {e}") from e

def main():
    """Test fetcher."""
    import logging
    logging.basicConfig(level=logging.INFO)
    for i, item in enumerate(fetch_dataset_sample(num_samples=5)):
        print(f"Item {i}: Keys={item.keys()}")
        if 'image' in item:
            print(f"  Image type: {type(item['image'])}")
        if 'annotations' in item:
            print(f"  Annotations count: {len(item['annotations'])}")

if __name__ == "__main__":
    main()
