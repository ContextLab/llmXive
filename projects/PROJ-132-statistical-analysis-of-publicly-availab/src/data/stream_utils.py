"""
Streaming utilities for the eBird dataset.

This module provides functions to stream the verified sample eBird dataset
in chunks to avoid memory overflow during processing.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Generator, Dict, Any, Iterator

import numpy as np
from datasets import load_dataset

from src.config import setup_logging

# Initialize logger
logger = setup_logging(__name__)


def stream_ebird_data(
    dataset_name: str = "vvud/eb-data",
    split: str = "train",
    streaming: bool = True,
    chunk_size: int = 1000
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream the eBird dataset in chunks.

    Args:
        dataset_name: The HuggingFace dataset name to load.
        split: The dataset split to use (default: "train").
        streaming: Whether to stream the dataset (default: True).
        chunk_size: Number of rows to yield per chunk (default: 1000).

    Yields:
        A dictionary representing a chunk of the dataset.

    Raises:
        RuntimeError: If the dataset cannot be loaded or streamed.
        MemoryError: If the chunk size is too large for available RAM.
    """
    logger.info(f"Starting to stream dataset: {dataset_name} (split={split})")

    try:
        # Load the dataset in streaming mode
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=streaming,
            trust_remote_code=True
        )
        logger.info(f"Successfully loaded dataset: {dataset_name}")
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise RuntimeError(f"Failed to load dataset {dataset_name}: {e}") from e

    # Estimate memory usage per row (rough heuristic)
    # This is a simplified check; in production, you might want a more robust check
    estimated_bytes_per_row = 1024  # 1KB per row as a rough estimate
    estimated_chunk_memory = chunk_size * estimated_bytes_per_row

    # Check if chunk size is too large (assuming ~6GB limit for safety)
    memory_limit = 6 * 1024 * 1024 * 1024  # 6 GB in bytes
    if estimated_chunk_memory > memory_limit:
        error_msg = (
            f"Chunk size {chunk_size} is too large for available RAM. "
            f"Estimated memory usage: {estimated_chunk_memory / (1024**3):.2f} GB. "
            f"Limit: {memory_limit / (1024**3):.2f} GB. "
            "Please reduce chunk_size."
        )
        logger.error(error_msg)
        raise MemoryError(error_msg)

    logger.info(f"Streaming with chunk size: {chunk_size}")

    current_chunk = []
    for idx, row in enumerate(dataset):
        current_chunk.append(row)

        if len(current_chunk) >= chunk_size:
            yield {
                "chunk_index": idx // chunk_size,
                "data": current_chunk,
                "num_rows": len(current_chunk)
            }
            current_chunk = []

    # Yield remaining rows
    if current_chunk:
        yield {
            "chunk_index": (idx // chunk_size) + 1 if idx >= chunk_size else 0,
            "data": current_chunk,
            "num_rows": len(current_chunk)
        }

    logger.info("Finished streaming dataset")


def process_streamed_chunks(
    chunk_generator: Generator[Dict[str, Any], None, None],
    process_func: callable
) -> None:
    """
    Process streamed chunks using a provided function.

    Args:
        chunk_generator: A generator yielding chunks of data.
        process_func: A function to apply to each chunk. It should accept
                      a dictionary with keys 'chunk_index', 'data', and 'num_rows'.
    """
    logger.info("Starting to process streamed chunks")

    try:
        for chunk in chunk_generator:
            logger.info(f"Processing chunk {chunk['chunk_index']} with {chunk['num_rows']} rows")
            process_func(chunk)
            logger.info(f"Finished processing chunk {chunk['chunk_index']}")
    except Exception as e:
        logger.error(f"Error processing chunks: {e}")
        raise


def main() -> None:
    """
    Main entry point for the streaming utility.

    This function demonstrates how to stream the eBird dataset and process
    the chunks. It is intended for testing and verification purposes.
    """
    logger.info("Starting stream_utils main")

    # Example: Stream the dataset and print chunk summaries
    def process_chunk(chunk: Dict[str, Any]) -> None:
        logger.info(f"Chunk {chunk['chunk_index']}: {chunk['num_rows']} rows")
        # Here you would typically process the chunk data
        # For example, filter, aggregate, or write to disk

    try:
        chunk_gen = stream_ebird_data(
            dataset_name="vvud/eb-data",
            split="train",
            streaming=True,
            chunk_size=1000
        )
        process_streamed_chunks(chunk_gen, process_chunk)
        logger.info("Successfully processed all chunks")
    except Exception as e:
        logger.error(f"Streaming or processing failed: {e}")
        sys.exit(1)

    logger.info("Stream_utils main completed")


if __name__ == "__main__":
    main()
