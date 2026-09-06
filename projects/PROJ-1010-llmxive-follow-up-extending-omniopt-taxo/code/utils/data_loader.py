"""
Streaming data loader for real datasets (TinyImageNet, C4).

Implements lazy streaming via HuggingFace datasets to handle large datasets
without loading everything into memory.

CRITICAL: This loader FAILS LOUDLY on missing real sources.
It does NOT fall back to synthetic data.
"""
import os
import sys
import logging
from typing import Dict, Any, Iterator, Optional, List, Tuple
from pathlib import Path

try:
    from datasets import load_dataset, DatasetDict
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Install it via: pip install datasets"
    )

# Import project utilities
from utils.logging import get_logger, error, info, warning
from utils.seeds import set_seed

logger = get_logger(__name__)


class DataLoaderError(Exception):
    """Custom exception for data loading failures."""
    pass


def validate_streaming_source(dataset_id: str, split: str = "train") -> bool:
    """
    Verify that a dataset exists and is accessible via streaming.
    
    Args:
        dataset_id: HuggingFace dataset identifier (e.g., 'tiny-imagenet-200')
        split: Dataset split to check
        
    Returns:
        True if accessible
        
    Raises:
        DataLoaderError: If the dataset is not found or streaming fails
    """
    try:
        # Attempt to stream just one example to verify access
        ds = load_dataset(dataset_id, split=split, streaming=True)
        # Try to get the first item
        next(iter(ds))
        return True
    except Exception as e:
        raise DataLoaderError(
            f"Real data source '{dataset_id}' (split={split}) is inaccessible: {e}. "
            "Ensure internet connectivity and correct dataset ID. "
            "No synthetic fallback is provided."
        ) from e


def load_tinyimagenet_streaming(
    split: str = "train",
    streaming: bool = True,
    seed: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Stream TinyImageNet dataset.
    
    Args:
        split: 'train', 'val', or 'test'
        streaming: Always True for memory efficiency
        seed: Optional seed for reproducibility if shuffling is needed
        
    Yields:
        Dictionary with 'image' (PIL Image) and 'label' (int)
        
    Raises:
        DataLoaderError: If the real dataset cannot be accessed
    """
    dataset_id = "tiny-imagenet-200"
    
    # Validate access first
    validate_streaming_source(dataset_id, split)
    
    if seed is not None:
        set_seed(seed)
        
    info(f"Loading real TinyImageNet ({split}) via streaming...")
    
    try:
        ds = load_dataset(
            dataset_id, 
            split=split, 
            streaming=streaming,
            trust_remote_code=True
        )
        
        # Iterate and yield
        for item in ds:
            yield item
            
    except Exception as e:
        error(f"Failed to stream TinyImageNet: {e}")
        raise DataLoaderError(
            "Failed to stream TinyImageNet dataset. "
            "Check internet connection and dataset availability. "
            "No synthetic fallback available."
        ) from e


def load_c4_streaming(
    split: str = "train",
    streaming: bool = True,
    seed: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Stream C4 dataset (real text corpus).
    
    Args:
        split: 'train' or 'validation'
        streaming: Always True for memory efficiency
        seed: Optional seed
        
    Yields:
        Dictionary with 'text' (str) and metadata
        
    Raises:
        DataLoaderError: If the real dataset cannot be accessed
    """
    # C4 is large; use a specific subset or configuration if needed
    # Using 'realnewslike' as a common configuration
    dataset_id = "c4"
    config_name = "realnewslike"
    
    if seed is not None:
        set_seed(seed)
        
    info(f"Loading real C4 ({config_name}/{split}) via streaming...")
    
    try:
        ds = load_dataset(
            dataset_id,
            name=config_name,
            split=split,
            streaming=streaming,
            trust_remote_code=True
        )
        
        for item in ds:
            yield item
            
    except Exception as e:
        error(f"Failed to stream C4: {e}")
        raise DataLoaderError(
            "Failed to stream C4 dataset. "
            "Check internet connection and dataset availability. "
            "No synthetic fallback available."
        ) from e


def get_sample_iterator(
    dataset_type: str,
    split: str = "train",
    max_samples: Optional[int] = None,
    seed: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Generic factory for dataset iterators.
    
    Args:
        dataset_type: 'tinyimagenet' or 'c4'
        split: Dataset split
        max_samples: Optional limit on number of samples to yield
        seed: Random seed
        
    Yields:
        Data samples
        
    Raises:
        DataLoaderError: If the dataset type is unknown or real data fails
    """
    if dataset_type.lower() == "tinyimagenet":
        iterator = load_tinyimagenet_streaming(split=split, seed=seed)
    elif dataset_type.lower() == "c4":
        iterator = load_c4_streaming(split=split, seed=seed)
    else:
        raise DataLoaderError(
            f"Unknown dataset type: {dataset_type}. "
            "Supported: 'tinyimagenet', 'c4'. "
            "No synthetic fallback available."
        )
    
    if max_samples:
        count = 0
        for item in iterator:
            yield item
            count += 1
            if count >= max_samples:
                break
    else:
        yield from iterator


def main():
    """
    CLI entry point for testing the streaming loader.
    
    Usage:
        python code/utils/data_loader.py --dataset tinyimagenet --split train --max 5
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test real data streaming loader")
    parser.add_argument("--dataset", type=str, default="tinyimagenet",
                        choices=["tinyimagenet", "c4"],
                        help="Dataset to load")
    parser.add_argument("--split", type=str, default="train",
                        help="Dataset split")
    parser.add_argument("--max", type=int, default=3,
                        help="Max samples to load for testing")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    
    args = parser.parse_args()
    
    try:
        info(f"Starting real data stream test: {args.dataset}/{args.split}")
        iterator = get_sample_iterator(
            args.dataset, 
            args.split, 
            max_samples=args.max,
            seed=args.seed
        )
        
        count = 0
        for sample in iterator:
            count += 1
            if args.dataset == "tinyimagenet":
                info(f"Sample {count}: Label={sample.get('label')}, Image type={type(sample.get('image'))}")
            elif args.dataset == "c4":
                info(f"Sample {count}: Text length={len(sample.get('text', ''))}")
                
        info(f"Successfully streamed {count} samples from real source.")
        
    except DataLoaderError as e:
        error(f"DATA LOADING FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()