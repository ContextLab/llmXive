"""
Streaming utilities for the eBird dataset.

This module provides functions to stream the verified sample eBird dataset
in chunks to avoid memory overflow during processing.
"""

import logging
from pathlib import Path
from typing import Iterator, Optional, Dict, Any, List

from datasets import load_dataset
import pandas as pd

from src.config import setup_logging

# Initialize logging
logger = setup_logging(__name__)


def stream_ebird_data(
    dataset_name: str = "vvud/eb-data",
    split: Optional[str] = None,
    columns: Optional[List[str]] = None,
    chunk_size: int = 10000
) -> Iterator[pd.DataFrame]:
    """
    Stream the eBird dataset in chunks.

    Args:
        dataset_name: The HuggingFace dataset name (default: "vvud/eb-data").
        split: The dataset split to use (e.g., "train", "test"). If None, streams all.
        columns: Optional list of columns to load. If None, loads all columns.
        chunk_size: Number of rows per chunk (default: 10000).

    Yields:
        pd.DataFrame: A chunk of the dataset as a pandas DataFrame.

    Raises:
        RuntimeError: If the dataset is not found or cannot be loaded.
        MemoryError: If the streaming fails due to memory issues.
    """
    logger.info(f"Starting stream for dataset: {dataset_name}")

    try:
        # Load dataset in streaming mode
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=True
        )

        logger.info(f"Successfully connected to dataset: {dataset_name}")

        # Iterate through the dataset in chunks
        buffer = []
        row_count = 0

        for row in dataset:
            buffer.append(row)
            row_count += 1

            if len(buffer) >= chunk_size:
                df = pd.DataFrame(buffer)
                if columns:
                    df = df[columns]
                yield df
                logger.debug(f"Yielded chunk of {len(df)} rows (total: {row_count})")
                buffer = []

        # Yield any remaining rows
        if buffer:
            df = pd.DataFrame(buffer)
            if columns:
                df = df[columns]
            yield df
            logger.info(f"Final chunk yielded: {len(df)} rows (total: {row_count})")

        logger.info(f"Streaming complete. Total rows processed: {row_count}")

    except Exception as e:
        logger.error(f"Failed to stream dataset {dataset_name}: {e}")
        # Re-raise to fail loudly as per requirements
        raise RuntimeError(f"Dataset streaming failed for {dataset_name}: {e}") from e


def get_dataset_info(
    dataset_name: str = "vvud/eb-data"
) -> Dict[str, Any]:
    """
    Get metadata about the dataset without loading data.

    Args:
        dataset_name: The HuggingFace dataset name.

    Returns:
        Dict with dataset metadata (splits, features, etc.).

    Raises:
        RuntimeError: If the dataset is not found.
    """
    logger.info(f"Fetching info for dataset: {dataset_name}")

    try:
        dataset = load_dataset(dataset_name, streaming=True)
        info = {
            "dataset_name": dataset_name,
            "splits": list(dataset.keys()) if hasattr(dataset, 'keys') else ["default"],
            "features": dataset.features if hasattr(dataset, 'features') else None
        }
        logger.info(f"Dataset info retrieved: {info}")
        return info
    except Exception as e:
        logger.error(f"Failed to get dataset info for {dataset_name}: {e}")
        raise RuntimeError(f"Failed to get dataset info for {dataset_name}: {e}") from e


def run_streaming_pipeline(
    output_dir: str = "data/interim",
    dataset_name: str = "vvud/eb-data",
    columns: Optional[List[str]] = None
) -> Path:
    """
    Run a streaming pipeline that processes the dataset in chunks.

    This function demonstrates the streaming capability by processing
    the dataset in chunks and writing intermediate results.

    Args:
        output_dir: Directory to write intermediate results.
        dataset_name: The HuggingFace dataset name.
        columns: Optional list of columns to process.

    Returns:
        Path to the output directory.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting streaming pipeline for {dataset_name}")

    chunk_count = 0
    total_rows = 0

    for chunk in stream_ebird_data(
        dataset_name=dataset_name,
        columns=columns,
        chunk_size=10000
    ):
        chunk_count += 1
        total_rows += len(chunk)

        # Process chunk (example: save to parquet)
        chunk_file = output_path / f"stream_chunk_{chunk_count:04d}.parquet"
        chunk.to_parquet(chunk_file)
        logger.debug(f"Wrote chunk {chunk_count} to {chunk_file}")

    logger.info(f"Streaming pipeline complete. Processed {total_rows} rows in {chunk_count} chunks.")

    # Write summary
    summary_file = output_path / "streaming_summary.json"
    summary_data = {
        "dataset_name": dataset_name,
        "total_chunks": chunk_count,
        "total_rows": total_rows,
        "output_directory": str(output_path)
    }

    import json
    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)

    logger.info(f"Summary written to {summary_file}")
    return output_path


def main():
    """Main entry point for testing the streaming utility."""
    logger.info("Running stream_utils.py main")

    # Get dataset info
    try:
        info = get_dataset_info("vvud/eb-data")
        print(f"Dataset Info: {info}")
    except RuntimeError as e:
        print(f"Error getting dataset info: {e}")
        return 1

    # Run streaming pipeline
    try:
        output_dir = run_streaming_pipeline(
            output_dir="data/interim/stream_test",
            dataset_name="vvud/eb-data",
            columns=["species", "lat", "lon", "date", "count", "checklist_id"]
        )
        print(f"Streaming pipeline completed. Output in: {output_dir}")
    except RuntimeError as e:
        print(f"Error running streaming pipeline: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
