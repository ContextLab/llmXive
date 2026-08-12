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
    Returns the current memory usage of the process in GB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def should_use_chunked_reading(threshold_gb: float = 3.0) -> bool:
    """
    Determines if chunked reading should be used based on memory usage.
    """
    current_mem = get_memory_usage_gb()
    return current_mem > threshold_gb

def read_csv_chunked(
    file_path: Path,
    chunksize: int = 10000,
    callback: Optional[Callable[[pd.DataFrame], None]] = None
) -> Iterator[pd.DataFrame]:
    """
    Reads a CSV file in chunks.
    Yields each chunk.
    """
    for chunk in pd.read_csv(file_path, chunksize=chunksize):
        if callback:
            callback(chunk)
        yield chunk

def load_dataframe_safely(
    file_path: Path,
    use_chunking: bool = False
) -> Optional[pd.DataFrame]:
    """
    Loads a dataframe safely, optionally using chunking.
    Returns None if loading fails.
    """
    try:
        if use_chunking or should_use_chunked_reading():
            logger.info("Using chunked loading due to memory constraints.")
            # For simplicity, we load all chunks and concatenate
            chunks = []
            for chunk in read_csv_chunked(file_path):
                chunks.append(chunk)
            return pd.concat(chunks, ignore_index=True)
        else:
            return pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to load dataframe: {e}")
        return None
