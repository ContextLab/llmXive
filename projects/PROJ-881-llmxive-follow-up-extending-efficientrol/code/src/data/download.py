"""
Dataset download module for GSM8K and MiniGrid.

This module provides functions to fetch datasets from HuggingFace Datasets
with strict constraints on sample size and memory usage.

CRITICAL: This module does NOT provide any synthetic fallbacks. If the
real data source is unavailable, it raises an exception immediately.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Iterator

# Use the project root to determine paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GSM8K_DATASET_ID = "gsm8k"
GSM8K_CONFIG = "main"  # Default config for GSM8K
MINIGRID_DATASET_ID = "Minigrid"  # Using the standard MiniGrid dataset from HuggingFace
MINIGRID_CONFIG = "minigrid"  # Default config

# Sample size limit as per FR-001
DEFAULT_SAMPLE_SIZE = 500

try:
    from datasets import load_dataset
except ImportError:
    logger.error("The 'datasets' package is required. Install it with: pip install datasets")
    raise


def download_gsm8k_subset(
    output_path: Optional[Path] = None,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    streaming: bool = True
) -> Path:
    """
    Download a subset of the GSM8K dataset from HuggingFace.
    
    Args:
        output_path: Path to save the dataset. Defaults to data/raw/gsm8k.jsonl
        sample_size: Maximum number of examples to download. Defaults to 500.
        streaming: If True, stream the dataset instead of loading all at once.
    
    Returns:
        Path to the saved JSONL file.
    
    Raises:
        ConnectionError: If the dataset cannot be fetched from HuggingFace.
        FileNotFoundError: If the dataset is not found.
    """
    if output_path is None:
        output_path = RAW_DATA_DIR / "gsm8k.jsonl"
    
    logger.info(f"Downloading GSM8K dataset (sample size: {sample_size})...")
    
    try:
        # Load dataset in streaming mode to handle large datasets efficiently
        dataset = load_dataset(
            GSM8K_DATASET_ID,
            GSM8K_CONFIG,
            split="train",
            streaming=streaming
        )
        
        # Apply sample size limit using itertools.islice
        # This ensures we only process the specified number of examples
        from itertools import islice
        sampled_data = list(islice(dataset, sample_size))
        
        logger.info(f"Successfully downloaded {len(sampled_data)} examples from GSM8K")
        
        # Write to JSONL file
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in sampled_data:
                f.write(json.dumps(example) + '\n')
        
        logger.info(f"GSM8K dataset saved to {output_path}")
        return output_path
        
    except Exception as e:
        # Re-raise with specific error types to fail loudly
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg.lower():
            raise FileNotFoundError(f"Dataset '{GSM8K_DATASET_ID}' not found on HuggingFace: {e}")
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            raise ConnectionError(f"Failed to connect to HuggingFace: {e}")
        else:
            raise ConnectionError(f"Failed to download GSM8K dataset: {e}")


def download_minigrid_subset(
    output_path: Optional[Path] = None,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    streaming: bool = True
) -> Path:
    """
    Download a subset of the MiniGrid dataset from HuggingFace.
    
    Args:
        output_path: Path to save the dataset. Defaults to data/raw/minigrid.jsonl
        sample_size: Maximum number of examples to download. Defaults to 500.
        streaming: If True, stream the dataset instead of loading all at once.
    
    Returns:
        Path to the saved JSONL file.
    
    Raises:
        ConnectionError: If the dataset cannot be fetched from HuggingFace.
        FileNotFoundError: If the dataset is not found.
    """
    if output_path is None:
        output_path = RAW_DATA_DIR / "minigrid.jsonl"
    
    logger.info(f"Downloading MiniGrid dataset (sample size: {sample_size})...")
    
    try:
        # Load dataset in streaming mode
        dataset = load_dataset(
            MINIGRID_DATASET_ID,
            MINIGRID_CONFIG,
            split="train",
            streaming=streaming
        )
        
        # Apply sample size limit using itertools.islice
        from itertools import islice
        sampled_data = list(islice(dataset, sample_size))
        
        logger.info(f"Successfully downloaded {len(sampled_data)} examples from MiniGrid")
        
        # Write to JSONL file
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in sampled_data:
                f.write(json.dumps(example) + '\n')
        
        logger.info(f"MiniGrid dataset saved to {output_path}")
        return output_path
        
    except Exception as e:
        # Re-raise with specific error types to fail loudly
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg.lower():
            raise FileNotFoundError(f"Dataset '{MINIGRID_DATASET_ID}' not found on HuggingFace: {e}")
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            raise ConnectionError(f"Failed to connect to HuggingFace: {e}")
        else:
            raise ConnectionError(f"Failed to download MiniGrid dataset: {e}")


def download_all_datasets(
    gsm8k_output: Optional[Path] = None,
    minigrid_output: Optional[Path] = None,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    streaming: bool = True
) -> Dict[str, Path]:
    """
    Download both GSM8K and MiniGrid datasets.
    
    Args:
        gsm8k_output: Path to save GSM8K dataset.
        minigrid_output: Path to save MiniGrid dataset.
        sample_size: Maximum number of examples for each dataset.
        streaming: If True, stream datasets instead of loading all at once.
    
    Returns:
        Dictionary mapping dataset name to output path.
    """
    results = {}
    
    try:
        gsm8k_path = download_gsm8k_subset(gsm8k_output, sample_size, streaming)
        results["gsm8k"] = gsm8k_path
    except Exception as e:
        logger.error(f"Failed to download GSM8K: {e}")
        raise
    
    try:
        minigrid_path = download_minigrid_subset(minigrid_output, sample_size, streaming)
        results["minigrid"] = minigrid_path
    except Exception as e:
        logger.error(f"Failed to download MiniGrid: {e}")
        raise
    
    return results


def main():
    """
    Main entry point for downloading datasets.
    
    Downloads both GSM8K and MiniGrid datasets with default parameters
    and prints the output paths.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download GSM8K and MiniGrid datasets")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help=f"Number of examples to download per dataset (default: {DEFAULT_SAMPLE_SIZE})"
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming mode (load entire dataset into memory)"
    )
    parser.add_argument(
        "--gsm8k-output",
        type=str,
        default=None,
        help="Path to save GSM8K dataset"
    )
    parser.add_argument(
        "--minigrid-output",
        type=str,
        default=None,
        help="Path to save MiniGrid dataset"
    )
    
    args = parser.parse_args()
    
    gsm8k_path = Path(args.gsm8k_output) if args.gsm8k_output else None
    minigrid_path = Path(args.minigrid_output) if args.minigrid_output else None
    
    results = download_all_datasets(
        gsm8k_output=gsm8k_path,
        minigrid_output=minigrid_path,
        sample_size=args.sample_size,
        streaming=not args.no_stream
    )
    
    print("\nDownload Summary:")
    for dataset_name, path in results.items():
        print(f"  {dataset_name}: {path}")


if __name__ == "__main__":
    main()
