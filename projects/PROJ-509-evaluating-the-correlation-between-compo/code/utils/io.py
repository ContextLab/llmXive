import pandas as pd
import psutil
import os
from pathlib import Path
from typing import Optional, Iterator, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024**3)


def should_use_chunked_reading(threshold_gb: float = 3.0) -> bool:
    """Decide whether to use chunked reading based on memory usage."""
    return get_memory_usage_gb() > threshold_gb


def read_csv_chunked(
    file_path: Path,
    chunk_size: int = 10000,
    func: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
) -> Iterator[pd.DataFrame]:
    """Read a CSV file in chunks and optionally apply a function."""
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        if func:
            chunk = func(chunk)
        yield chunk


def load_dataframe_safely(file_path: Path, chunk_size: int = 10000) -> pd.DataFrame:
    """Load a dataframe, using chunked reading if memory is constrained."""
    if should_use_chunked_reading():
        logger.info("Using chunked reading due to memory constraints")
        chunks = []
        for chunk in read_csv_chunked(file_path, chunk_size):
            chunks.append(chunk)
        return pd.concat(chunks, ignore_index=True)
    else:
        return pd.read_csv(file_path)
