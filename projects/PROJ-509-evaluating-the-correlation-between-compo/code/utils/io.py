"""
I/O utilities for handling large datasets.
"""
import pandas as pd
import psutil
import os
from pathlib import Path
from typing import Optional, Iterator, Dict, Any, Callable
import logging

from .logging import get_logger


logger = get_logger(__name__)


def get_memory_usage_gb() -> float:
    """
    Get current memory usage in GB.

    Returns:
        Current memory usage in GB.
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / (1024 ** 3)


def should_use_chunked_reading(file_path: str, threshold_gb: float = 2.0) -> bool:
    """
    Determine if chunked reading should be used based on file size.

    Args:
        file_path: Path to the file.
        threshold_gb: Threshold in GB above which chunked reading is recommended.

    Returns:
        True if chunked reading is recommended, False otherwise.
    """
    try:
        file_size_bytes = os.path.getsize(file_path)
        file_size_gb = file_size_bytes / (1024 ** 3)
        return file_size_gb > threshold_gb
    except OSError:
        logger.warning(f"Could not get file size for {file_path}, defaulting to chunked reading.")
        return True


def read_csv_chunked(
    file_path: str,
    chunksize: int = 100000,
    callback: Optional[Callable[[pd.DataFrame], None]] = None,
    **kwargs
) -> Iterator[pd.DataFrame]:
    """
    Read a CSV file in chunks.

    Args:
        file_path: Path to the CSV file.
        chunksize: Number of rows per chunk.
        callback: Optional callback function to process each chunk.
        **kwargs: Additional arguments to pass to pandas.read_csv.

    Yields:
        DataFrames containing chunks of the data.
    """
    logger.info(f"Reading {file_path} in chunks of {chunksize} rows.")

    for chunk in pd.read_csv(file_path, chunksize=chunksize, **kwargs):
        if callback:
            callback(chunk)
        yield chunk


def load_dataframe_safely(
    file_path: str,
    max_memory_gb: float = 4.0,
    **kwargs
) -> pd.DataFrame:
    """
    Load a DataFrame safely, using chunked reading if necessary.

    Args:
        file_path: Path to the CSV file.
        max_memory_gb: Maximum memory to use before switching to chunked reading.
        **kwargs: Additional arguments to pass to pandas.read_csv or read_csv_chunked.

    Returns:
        The loaded DataFrame.
    """
    current_memory = get_memory_usage_gb()
    available_memory = max_memory_gb - current_memory

    if available_memory <= 0:
        logger.warning("No available memory for loading, using chunked reading.")
        # If we can't load the whole file, we need to handle it differently
        # For now, raise an error
        raise MemoryError(
            f"Not enough available memory. Current usage: {current_memory:.2f}GB, "
            f"Max allowed: {max_memory_gb}GB"
        )

    # Estimate file size
    try:
        file_size_bytes = os.path.getsize(file_path)
        file_size_gb = file_size_bytes / (1024 ** 3)

        if file_size_gb > available_memory * 0.8:
            # File is too large to load in one go
            logger.info(f"File size ({file_size_gb:.2f}GB) exceeds available memory. "
                        f"Using chunked reading and concatenating.")
            chunks = []
            for chunk in read_csv_chunked(file_path, **kwargs):
                chunks.append(chunk)
            return pd.concat(chunks, ignore_index=True)
    except OSError:
        logger.warning(f"Could not determine file size for {file_path}, attempting direct load.")

    # Try direct load
    try:
        df = pd.read_csv(file_path, **kwargs)
        return df
    except MemoryError:
        logger.error(f"Failed to load {file_path} directly due to memory constraints.")
        raise
