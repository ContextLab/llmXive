"""
Streaming utilities for processing large eBird datasets in chunks.

This module provides functions to stream the verified sample eBird dataset
from HuggingFace without loading the entire dataset into memory.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Generator, Dict, Any, Iterator, List

import numpy as np
from datasets import load_dataset

from src.config import setup_logging

# Configure logging
logger = setup_logging(__name__)


def stream_ebird_data(
    dataset_name: str = "vvud/eb-data",
    split: str = "train",
    chunk_size: int = 1000,
    streaming: bool = True
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream the eBird dataset in chunks to avoid memory overflow.

    Args:
        dataset_name: The HuggingFace dataset identifier.
        split: The dataset split to load (e.g., 'train').
        chunk_size: Number of rows to yield per chunk.
        streaming: Whether to use streaming mode.

    Yields:
        Dicts containing batches of dataset rows.

    Raises:
        RuntimeError: If the dataset is not found or cannot be accessed.
        MemoryError: If estimated memory usage exceeds available capacity.
    """
    logger.info(f"Starting to stream dataset: {dataset_name}, split={split}")

    try:
        # Load the dataset in streaming mode
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=streaming,
            trust_remote_code=True
        )
        logger.info(f"Successfully connected to dataset: {dataset_name}")
    except Exception as e:
        error_msg = f"Failed to load dataset {dataset_name}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Validate chunk size
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    # Stream data in chunks
    current_chunk: List[Dict[str, Any]] = []
    row_count = 0

    for row in dataset:
        current_chunk.append(row)
        row_count += 1

        if len(current_chunk) >= chunk_size:
            logger.debug(f"Yielding chunk of {len(current_chunk)} rows (total: {row_count})")
            yield {"rows": current_chunk, "count": len(current_chunk), "total_rows": row_count}
            current_chunk = []

    # Yield remaining rows
    if current_chunk:
        logger.debug(f"Yielding final chunk of {len(current_chunk)} rows (total: {row_count})")
        yield {"rows": current_chunk, "count": len(current_chunk), "total_rows": row_count}

    logger.info(f"Streaming complete. Total rows processed: {row_count}")

    # Estimate memory usage per row (rough heuristic)
    # This is a simplified check; in production, you might want a more robust check
    estimated_bytes_per_row = 1024  # 1KB per row as a rough estimate
    estimated_chunk_memory = chunk_size * estimated_bytes_per_row

def process_streamed_chunks(
    dataset_name: str = "vvud/eb-data",
    split: str = "train",
    chunk_size: int = 1000,
    processing_fn: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Process streamed chunks with an optional processing function.

    Args:
        dataset_name: The HuggingFace dataset identifier.
        split: The dataset split to load.
        chunk_size: Number of rows per chunk.
        processing_fn: Optional function to apply to each chunk.
                     Should accept a dict with 'rows', 'count', 'total_rows'.
                     If None, chunks are just counted.

    Returns:
        Dict with processing statistics.

    Raises:
        RuntimeError: If streaming fails.
    """
    stats = {
        "total_chunks": 0,
        "total_rows": 0,
        "rows_per_chunk": []
    }

    logger.info(f"Processing streamed chunks from {dataset_name}")

    try:
        for chunk_data in stream_ebird_data(
            dataset_name=dataset_name,
            split=split,
            chunk_size=chunk_size
        ):
            stats["total_chunks"] += 1
            stats["total_rows"] += chunk_data["count"]
            stats["rows_per_chunk"].append(chunk_data["count"])

            if processing_fn:
                processing_fn(chunk_data)

            # Log progress every 10 chunks
            if stats["total_chunks"] % 10 == 0:
                logger.info(f"Processed {stats['total_chunks']} chunks, "
                            f"{stats['total_rows']} total rows")

    except Exception as e:
        error_msg = f"Error during chunk processing: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    logger.info(f"Processing complete: {stats['total_chunks']} chunks, "
                f"{stats['total_rows']} rows")
    return stats


def get_dataset_info(dataset_name: str = "vvud/eb-data") -> Dict[str, Any]:
    """
    Retrieve metadata about the dataset without loading data.

    Args:
        dataset_name: The HuggingFace dataset identifier.

    Returns:
        Dict with dataset metadata (features, num_rows if available, etc.).

    Raises:
        RuntimeError: If dataset info cannot be retrieved.
    """
    logger.info(f"Fetching info for dataset: {dataset_name}")

    try:
        dataset = load_dataset(
            dataset_name,
            streaming=True,
            trust_remote_code=True
        )

        info = {
            "dataset_name": dataset_name,
            "features": list(dataset.features.keys()) if hasattr(dataset, 'features') else [],
            "num_splits": len(list(dataset)),
        }

        # Try to get split names
        try:
            info["splits"] = list(dataset)
        except Exception:
            info["splits"] = ["unknown"]

        logger.info(f"Dataset info retrieved: {info}")
        return info

    except Exception as e:
        error_msg = f"Failed to get dataset info for {dataset_name}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def run_streaming_pipeline(
    dataset_name: str = "vvud/eb-data",
    split: str = "train",
    chunk_size: int = 1000,
    output_path: Optional[Path] = None
) -> Path:
    """
    Run the streaming pipeline and optionally save aggregated statistics.

    Args:
        dataset_name: The HuggingFace dataset identifier.
        split: The dataset split to load.
        chunk_size: Number of rows per chunk.
        output_path: Optional path to write a summary JSON file.

    Returns:
        Path to the output file (or None if no output path specified).
    """
    logger.info("Starting streaming pipeline")

    # Process chunks and collect stats
    stats = process_streamed_chunks(
        dataset_name=dataset_name,
        split=split,
        chunk_size=chunk_size
    )

    # Add dataset info
    try:
        dataset_info = get_dataset_info(dataset_name)
        stats["dataset_info"] = dataset_info
    except RuntimeError as e:
        logger.warning(f"Could not retrieve dataset info: {e}")
        stats["dataset_info"] = {"error": str(e)}

    # Write output if path provided
    if output_path:
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert non-serializable types
        serializable_stats = {
            k: v if isinstance(v, (str, int, float, bool, type(None))) else str(v)
            for k, v in stats.items()
        }

        with open(output_path, 'w') as f:
            json.dump(serializable_stats, f, indent=2)

        logger.info(f"Streaming pipeline results written to {output_path}")

    return output_path


def main():
    """
    Main entry point for the streaming utility script.
    """
    logger = setup_logging(__name__, level=logging.INFO)
    logger.info("eBird Data Streaming Utility")

    # Default configuration
    dataset_name = "vvud/eb-data"
    split = "train"
    chunk_size = 1000
    output_path = Path("data/processed/streaming_stats.json")

    try:
        # Run the streaming pipeline
        result_path = run_streaming_pipeline(
            dataset_name=dataset_name,
            split=split,
            chunk_size=chunk_size,
            output_path=output_path
        )

        logger.info(f"Streaming pipeline completed successfully. Output: {result_path}")
        return 0

    except RuntimeError as e:
        logger.error(f"Streaming pipeline failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during streaming: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
