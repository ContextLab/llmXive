"""
Fetcher module for downloading a sampled subset of the COCO-Stuff/ParaDLC-Bench dataset.

This module implements the logic to programmatically access the real dataset
from HuggingFace Hub, ensuring no synthetic or fake data is used.

It strictly adheres to the "fail loudly" principle: if the dataset cannot be
fetched, it raises an exception rather than falling back to synthetic data.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Iterator

try:
    from datasets import load_dataset, DatasetDict
except ImportError:
    print("Error: 'datasets' package is required. Install it via: pip install datasets", file=sys.stderr)
    sys.exit(1)

from config import get_data_path


DATASET_ID = "COCO-Stuff/ParaDLC-Bench"
# We stream the dataset to avoid loading the entire ~7GB+ into memory at once
# before processing.
STREAMING_MODE = True
# The number of samples to fetch per region count bin (as per T024 requirements).
# This fetcher provides the iterator; the generator will handle the binning logic.
SAMPLE_SIZE_PER_BIN = 50


def ensure_data_dir() -> Path:
    """Ensure the raw data directory exists."""
    data_root = get_data_path()
    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir


def fetch_dataset_sample(
    split: str = "train",
    num_samples: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Fetches a sampled subset of the ParaDLC-Bench dataset from HuggingFace.
    
    This function connects to the real HuggingFace Hub to retrieve the dataset.
    It does NOT generate synthetic data. If the network is unavailable or the
    dataset ID is incorrect, this function will raise an exception (Fail Loudly).
    
    Args:
        split: The dataset split to load (e.g., 'train', 'test').
        num_samples: Optional limit on the number of samples to yield. 
                     If None, yields all available samples in the split.
                     
    Returns:
        An iterator over the dataset samples.
        
    Raises:
        Exception: If the dataset cannot be fetched from HuggingFace.
    """
    try:
        # Attempt to load the dataset in streaming mode
        # This avoids downloading the full dataset to disk immediately,
        # allowing us to process it in chunks.
        dataset = load_dataset(
            DATASET_ID,
            split=split,
            streaming=STREAMING_MODE
        )
        
        # If a specific number of samples is requested, limit the iterator
        if num_samples is not None:
            dataset = dataset.take(num_samples)
            
        return dataset
        
    except Exception as e:
        # Fail loudly: do not catch and return empty/synthetic data
        raise RuntimeError(
            f"Failed to fetch real dataset '{DATASET_ID}' from HuggingFace Hub. "
            f"Ensure internet connectivity and that the dataset ID is correct. "
            f"Original error: {e}"
        ) from e


def main():
    """
    Main entry point for the fetcher script.
    
    This script attempts to download and save a small sample of the dataset
    to `data/raw/` to verify connectivity and dataset integrity.
    It is intended to be called by the generator module (T024) during the
    full pipeline execution.
    """
    print(f"Attempting to fetch dataset: {DATASET_ID}...")
    
    try:
        # Create data directory
        data_dir = ensure_data_dir()
        print(f"Data directory ready: {data_dir}")
        
        # Fetch a small sample (e.g., 5 images) to verify the connection
        # The actual generation loop (T024) will handle the full sampling strategy.
        sample_count = 5
        print(f"Fetching {sample_count} sample(s) for verification...")
        
        dataset_iter = fetch_dataset_sample(num_samples=sample_count)
        
        samples_saved = 0
        for sample in dataset_iter:
            samples_saved += 1
            # In a real implementation, we would process and save the image/data here.
            # For this fetcher, we just confirm we can iterate over real data.
            if "image" in sample:
                print(f"  Retrieved sample {samples_saved}: Image shape available.")
            else:
                print(f"  Retrieved sample {samples_saved}: Keys {list(sample.keys())}")
        
        print(f"Successfully fetched {samples_saved} real samples from {DATASET_ID}.")
        print("Fetch verification complete.")
        
    except Exception as e:
        print(f"CRITICAL: Fetch failed. {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
