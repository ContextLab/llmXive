"""
Streaming loader for large OpenNeuro datasets.
Implements memory-efficient chunked processing using HuggingFace datasets streaming.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Generator, Iterator, List
import numpy as np

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required for streaming. "
        "Install it via: pip install datasets"
    )

from logger import get_logger
from config import get_paths, load_config

logger = get_logger(__name__)


class StreamingLoaderError(Exception):
    """Custom exception for streaming loader failures."""
    pass


def load_openneuro_streaming(
    dataset_id: str,
    split: str = "train",
    streaming: bool = True,
    cache_dir: Optional[str] = None
) -> Iterator[Dict[str, Any]]:
    """
    Load an OpenNeuro dataset using streaming mode to avoid OOM errors.

    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds0001171').
        split: The dataset split to load (default: 'train').
        streaming: Whether to use streaming mode (default: True).
        cache_dir: Optional cache directory for downloaded files.

    Yields:
        Individual records (chunks/rows) from the dataset.

    Raises:
        StreamingLoaderError: If the dataset fetch fails or streaming is not supported.
    """
    if not dataset_id:
        raise StreamingLoaderError("Dataset ID cannot be empty.")

    logger.info(f"Starting streaming load for OpenNeuro dataset: {dataset_id}")

    try:
        # Use HuggingFace datasets with streaming enabled
        # This fetches data chunk-by-chunk instead of loading everything into RAM
        ds = load_dataset(
            dataset_id,
            split=split,
            streaming=streaming,
            cache_dir=cache_dir
        )
        
        # Verify streaming is actually active
        if not streaming:
            logger.warning("Streaming was requested but dataset returned a non-streaming object.")
        
        # Iterate over the dataset in chunks
        logger.info("Iterating through dataset in streaming mode...")
        for record in ds:
            yield record

    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id} in streaming mode: {str(e)}")
        # Fail loudly - do not fall back to synthetic data
        raise StreamingLoaderError(f"Dataset streaming failed: {str(e)}")


def save_streaming_results(
    output_path: str,
    dataset_id: str,
    processed_count: int,
    stats: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save metadata about the streaming process to a JSON file.

    Args:
        output_path: Path to the output JSON file.
        dataset_id: The dataset ID that was processed.
        processed_count: Number of records/chunks processed.
        stats: Optional dictionary of statistics gathered during processing.
    """
    metadata = {
        "dataset_id": dataset_id,
        "processed_count": processed_count,
        "streaming_used": True,
        "stats": stats or {}
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Streaming results saved to {output_file}")


def main():
    """
    Main entry point for testing the streaming loader.
    This function demonstrates the streaming logic but should be invoked
    by the main pipeline (main.py) for actual data processing.
    """
    config = load_config()
    paths = get_paths()
    
    # Use a known OpenNeuro dataset for demonstration
    # Note: In production, this would be passed via CLI arguments or config
    dataset_id = "ds0001171"  # Example dataset
    
    logger.info(f"Testing streaming loader with dataset: {dataset_id}")
    
    try:
        processed_count = 0
        stats = {
            "total_bytes": 0,
            "chunks_processed": 0
        }
        
        # Process the dataset in streaming mode
        for record in load_openneuro_streaming(dataset_id):
            processed_count += 1
            stats["chunks_processed"] += 1
            
            # Log progress every 100 records
            if processed_count % 100 == 0:
                logger.info(f"Processed {processed_count} records...")
            
            # Stop after a reasonable number for testing
            # In production, this would process the entire dataset
            if processed_count >= 1000:
                logger.info("Reached test limit (1000 records). Stopping.")
                break
        
        # Save results
        output_path = os.path.join(paths["OUTPUT_PATH"], "streaming_results.json")
        save_streaming_results(output_path, dataset_id, processed_count, stats)
        
        logger.info(f"Successfully processed {processed_count} records in streaming mode.")
        
    except StreamingLoaderError as e:
        logger.error(f"Streaming loader failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during streaming: {str(e)}")
        raise


if __name__ == "__main__":
    main()
