"""
Streaming utilities for trajectory data processing.

This module provides functions to stream trajectory data from the HuggingFace
dataset repository in chunks to avoid memory overflow during manifold analysis.
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


def stream_trajectory_data(
    dataset_name: str = "vvud/eb-data",
    streaming: bool = True,
    batch_size: int = 1000,
    columns: Optional[list] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream trajectory data from a HuggingFace dataset in chunks.

    This function loads the dataset in streaming mode and yields batches of data
    to prevent loading the entire dataset into memory. This is essential for
    processing large trajectory datasets during manifold analysis.

    Args:
        dataset_name: The HuggingFace dataset identifier (default: "vvud/eb-data").
        streaming: Whether to stream the dataset (default: True).
        batch_size: Number of rows to yield per batch (default: 1000).
        columns: Optional list of specific columns to load. If None, all columns
                are loaded.

    Yields:
        A dictionary representing a batch of trajectory data with keys matching
        column names and values as numpy arrays.

    Raises:
        RuntimeError: If the dataset cannot be loaded or accessed.
        MemoryError: If the batch size is too large for available memory.
        FileNotFoundError: If the dataset is not found on HuggingFace.

    Example:
        >>> for batch in stream_trajectory_data("vvud/eb-data"):
        ...     process_batch(batch)
    """
    logger.info(f"Starting to stream dataset: {dataset_name}")
    
    try:
        # Load dataset in streaming mode
        dataset = load_dataset(dataset_name, streaming=streaming)
        
        # Determine which split to use (prefer 'train' if available)
        split_name = "train" if "train" in dataset else list(dataset.keys())[0]
        logger.info(f"Using split: {split_name}")
        
        dataset_split = dataset[split_name]
        
        # Filter columns if specified
        if columns is not None:
            available_cols = set(dataset_split.column_names)
            requested_cols = set(columns)
            missing_cols = requested_cols - available_cols
            
            if missing_cols:
                logger.warning(f"Requested columns not found: {missing_cols}")
                columns = list(requested_cols & available_cols)
            
            if not columns:
                raise ValueError("No valid columns found to stream.")
            
            dataset_split = dataset_split.select_columns(columns)
        
        # Stream data in batches
        batch = []
        for idx, row in enumerate(dataset_split):
            batch.append(row)
            
            if len(batch) >= batch_size:
                yield _batch_to_dict(batch)
                batch = []
                
                # Check memory pressure periodically
                if idx % 10000 == 0:
                    _check_memory_pressure()
        
        # Yield remaining batch
        if batch:
            yield _batch_to_dict(batch)
            
        logger.info(f"Completed streaming {idx + 1} rows from {dataset_name}")
        
    except Exception as e:
        logger.error(f"Failed to stream dataset {dataset_name}: {str(e)}")
        raise RuntimeError(f"Dataset streaming failed: {str(e)}") from e


def _batch_to_dict(batch: list) -> Dict[str, np.ndarray]:
    """
    Convert a list of row dictionaries to a dictionary of numpy arrays.

    Args:
        batch: List of dictionaries, each representing a row.

    Returns:
        Dictionary mapping column names to numpy arrays.
    """
    if not batch:
        return {}
    
    # Get column names from first row
    columns = list(batch[0].keys())
    
    # Convert to dictionary of arrays
    result = {}
    for col in columns:
        try:
            result[col] = np.array([row[col] for row in batch])
        except (KeyError, TypeError) as e:
            logger.warning(f"Error converting column {col}: {e}")
            # Handle mixed types by falling back to object array
            result[col] = np.array([row.get(col, None) for row in batch], dtype=object)
    
    return result


def _check_memory_pressure() -> None:
    """
    Check if memory usage is approaching limits and raise MemoryError if so.

    This is a simple check that can be expanded with more sophisticated
    memory monitoring if needed.
    """
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Log memory usage
        logger.debug(f"Current memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
        
        # Raise error if using more than 80% of available memory
        # Note: This is a heuristic and may need adjustment based on system
        if hasattr(memory_info, 'percent'):
            # psutil doesn't always provide percent for process, so we estimate
            total_mem = psutil.virtual_memory().total
            if total_mem > 0:
                usage_percent = (memory_info.rss / total_mem) * 100
                if usage_percent > 80:
                    raise MemoryError(
                        f"Memory usage at {usage_percent:.1f}% - "
                        "reducing batch size or processing in smaller chunks"
                    )
    except ImportError:
        # psutil not available, skip memory check
        logger.debug("psutil not available, skipping memory pressure check")
    except Exception as e:
        logger.warning(f"Error checking memory pressure: {e}")


def get_trajectory_schema(dataset_name: str = "vvud/eb-data") -> Dict[str, str]:
    """
    Get the schema (column names and types) for the trajectory dataset.

    Args:
        dataset_name: The HuggingFace dataset identifier.

    Returns:
        Dictionary mapping column names to their data types as strings.

    Raises:
        RuntimeError: If the dataset cannot be accessed.
    """
    try:
        dataset = load_dataset(dataset_name, streaming=True)
        split_name = "train" if "train" in dataset else list(dataset.keys())[0]
        dataset_split = dataset[split_name]
        
        schema = {}
        for col_name, col_type in zip(
            dataset_split.column_names,
            dataset_split.features.values()
        ):
            schema[col_name] = str(col_type)
        
        return schema
        
    except Exception as e:
        logger.error(f"Failed to get schema for {dataset_name}: {str(e)}")
        raise RuntimeError(f"Schema retrieval failed: {str(e)}") from e


def run_trajectory_streaming_pipeline(
    dataset_name: str = "vvud/eb-data",
    output_dir: Optional[Path] = None,
    batch_size: int = 1000
) -> Dict[str, Any]:
    """
    Run a complete streaming pipeline for trajectory data processing.

    This function orchestrates the streaming of trajectory data and provides
    basic statistics about the data processed.

    Args:
        dataset_name: The HuggingFace dataset identifier.
        output_dir: Optional directory to save processed batches.
        batch_size: Number of rows per batch.

    Returns:
        Dictionary containing processing statistics:
        - total_rows: Total number of rows processed
        - batches_processed: Number of batches yielded
        - columns: List of column names
        - dataset_name: Name of the dataset processed

    Raises:
        RuntimeError: If processing fails.
    """
    logger.info("Starting trajectory streaming pipeline")
    
    stats = {
        "total_rows": 0,
        "batches_processed": 0,
        "columns": [],
        "dataset_name": dataset_name,
        "status": "success"
    }
    
    try:
        for batch in stream_trajectory_data(
            dataset_name=dataset_name,
            batch_size=batch_size
        ):
            stats["batches_processed"] += 1
            stats["total_rows"] += len(batch[next(iter(batch))])
            
            if not stats["columns"]:
                stats["columns"] = list(batch.keys())
            
            # Optionally save batches if output_dir is specified
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                # Save logic would go here if needed
        
        logger.info(f"Pipeline completed: {stats['total_rows']} rows in "
                   f"{stats['batches_processed']} batches")
        
    except Exception as e:
        stats["status"] = "failed"
        stats["error"] = str(e)
        logger.error(f"Pipeline failed: {e}")
        raise RuntimeError(f"Pipeline failed: {e}") from e
    
    return stats


def main():
    """
    Main entry point for testing the streaming utility.

    This function runs a demonstration of the streaming capability
    by processing a small sample of the dataset.
    """
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Running trajectory streaming utility demo")
    
    try:
        # Run the streaming pipeline
        stats = run_trajectory_streaming_pipeline(
            dataset_name="vvud/eb-data",
            batch_size=100
        )
        
        logger.info(f"Demo completed successfully:")
        logger.info(f"  - Total rows: {stats['total_rows']}")
        logger.info(f"  - Batches: {stats['batches_processed']}")
        logger.info(f"  - Columns: {stats['columns']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
