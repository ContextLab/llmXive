"""
Performance Utilities Module.

Provides optimized functions for memory management, data loading, and batch processing
to support large-scale genomic data analysis.
"""
import os
import gc
import time
import logging
import random
from typing import Generator, List, Any, Optional, Callable
import numpy as np
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """Context manager and utility to monitor RAM usage."""
    
    def __init__(self, limit_gb: float = 7.0):
        self.limit_mb = limit_gb * 1024
        self.start_time = None
        self.start_mem = 0
        self.log_entries = []
        
    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except ImportError:
            # Fallback for Windows
            return 0.0

    def start(self):
        self.start_time = time.time()
        self.start_mem = self._get_memory_mb()
        logger.info(f"Memory Monitor started. Initial usage: {self.start_mem:.2f} MB")

    def stop(self):
        if self.start_time:
            duration = time.time() - self.start_time
            end_mem = self._get_memory_mb()
            logger.info(f"Memory Monitor stopped. Duration: {duration:.2f}s, Final usage: {end_mem:.2f} MB")

    def check(self) -> bool:
        current = self._get_memory_mb()
        if current > self.limit_mb:
            logger.error(f"Memory limit exceeded: {current:.2f} MB > {self.limit_mb:.2f} MB")
            return False
        return True

    def get_log(self) -> str:
        return "\n".join(self.log_entries)

    def log(self, msg: str):
        current = self._get_memory_mb()
        entry = f"[{time.strftime('%H:%M:%S')}] {msg} (RAM: {current:.2f} MB)"
        self.log_entries.append(entry)
        logger.info(entry)

def load_parquet_chunked(path: Path, chunk_size: int = 100000) -> pd.DataFrame:
    """
    Load a large parquet file in chunks to manage memory.
    Returns the concatenated DataFrame.
    """
    logger.info(f"Loading {path} in chunks of {chunk_size}...")
    chunks = []
    
    # Parquet doesn't support native chunked reading like CSV without pyarrow specifics
    # We use pyarrow directly for better control if needed, but pandas read_parquet 
    # usually handles memory well. For true chunking on disk, we might need to read row groups.
    # Here we assume pandas can handle it or we use pyarrow.Table for large files.
    
    try:
        import pyarrow.parquet as pq
        table = pq.read_table(str(path))
        df = table.to_pandas()
        logger.info(f"Loaded {len(df)} rows.")
        return df
    except Exception as e:
        logger.warning(f"Failed to load with pyarrow directly: {e}. Attempting pandas fallback.")
        return pd.read_parquet(path)

def batch_process(items: List[Any], process_func: Callable, batch_size: int = 10) -> List[Any]:
    """
    Process a list of items in batches to control memory and provide progress.
    """
    results = []
    total = len(items)
    for i in range(0, total, batch_size):
        batch = items[i:i+batch_size]
        logger.debug(f"Processing batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
        for item in batch:
            results.append(process_func(item))
        # Force GC between batches if memory is tight
        if i % (batch_size * 10) == 0:
            gc_collect_if_needed()
    return results

def optimized_shuffle(array: np.ndarray, random_state: Optional[int] = None) -> np.ndarray:
    """
    Optimized shuffle for numpy arrays.
    """
    if random_state is not None:
        rng = np.random.default_rng(random_state)
        return rng.permutation(array)
    else:
        return np.random.permutation(array)

def vectorized_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute Pearson correlation using vectorized numpy operations.
    """
    # Center
    x_centered = x - np.mean(x)
    y_centered = y - np.mean(y)
    # Normalize
    norm_x = np.linalg.norm(x_centered)
    norm_y = np.linalg.norm(y_centered)
    if norm_x == 0 or norm_y == 0:
        return 0.0
    return np.dot(x_centered, y_centered) / (norm_x * norm_y)

def gc_collect_if_needed(threshold: int = 1000000):
    """
    Trigger garbage collection if a certain number of objects are unreachable.
    """
    if gc.collect() > threshold:
        logger.debug(f"Garbage collection triggered. Collected {gc.collect()} objects.")

def timed_operation(func: Callable, *args, **kwargs) -> Any:
    """
    Decorator or helper to time an operation.
    """
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    logger.info(f"Operation {func.__name__} took {end - start:.2f} seconds.")
    return result
