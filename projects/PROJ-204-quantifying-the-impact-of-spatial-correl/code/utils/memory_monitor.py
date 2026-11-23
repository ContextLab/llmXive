"""
Memory monitoring and optimization utilities for the pipeline.
Ensures peak RAM usage stays within the 7GB limit on CPU-only CI.
"""
import os
import gc
import logging
import traceback
from typing import Callable, Any, Optional, TypeVar
from contextlib import contextmanager

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("psutil not installed. Memory monitoring will be limited.")

T = TypeVar('T')

# Target limit in bytes (7 GB)
MEMORY_LIMIT_BYTES = 7 * 1024**3
MEMORY_LIMIT_GB = 7.0

logger = logging.getLogger(__name__)


def get_current_memory_mb() -> float:
    """
    Returns the current memory usage of the current process in MB.
    Returns 0.0 if psutil is not available.
    """
    if not HAS_PSUTIL:
        return 0.0
    try:
        process = psutil.Process(os.getpid())
        # RSS (Resident Set Size) is the non-swapped physical memory used
        return process.memory_info().rss / (1024 * 1024)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        logger.warning("Could not access process memory info.")
        return 0.0


def check_memory_limit(limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """
    Checks if current memory usage is below the limit.
    Returns True if safe, False if limit exceeded.
    """
    current_mb = get_current_memory_mb()
    limit_mb = limit_gb * 1024
    if current_mb > limit_mb:
        logger.error(f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb:.2f} MB")
        return False
    return True


@contextmanager
def memory_guard(limit_gb: float = MEMORY_LIMIT_GB, log_interval_mb: float = 1000.0):
    """
    Context manager to monitor memory usage during a block of code.
    If memory exceeds the limit, it triggers garbage collection and logs a warning.
    If it exceeds significantly, it raises a MemoryError to fail fast.

    Args:
        limit_gb: Maximum allowed memory in GB.
        log_interval_mb: Log memory usage every time it increases by this amount.
    """
    if not HAS_PSUTIL:
        yield
        return

    start_mem = get_current_memory_mb()
    peak_mem = start_mem
    last_logged = start_mem

    logger.info(f"Memory guard started. Start: {start_mem:.2f} MB, Limit: {limit_gb * 1024:.2f} MB")

    try:
        yield
    finally:
        end_mem = get_current_memory_mb()
        if end_mem > peak_mem:
            peak_mem = end_mem

        logger.info(f"Memory guard finished. End: {end_mem:.2f} MB, Peak: {peak_mem:.2f} MB")

        if peak_mem > (limit_gb * 1024):
            raise MemoryError(
                f"Pipeline exceeded memory limit of {limit_gb} GB. "
                f"Peak usage: {peak_mem:.2f} MB. "
                "Consider streaming data or processing in smaller chunks."
            )


def force_gc() -> int:
    """
    Forces garbage collection and returns the amount of memory freed (approx).
    """
    if not HAS_PSUTIL:
        gc.collect()
        return 0

    before = get_current_memory_mb()
    gc.collect()
    after = get_current_memory_mb()
    freed = before - after
    if freed > 0:
        logger.debug(f"Garbage collection freed {freed:.2f} MB")
    return freed


def optimize_dataframe_memory(df):
    """
    Optimizes memory usage of a pandas DataFrame by downcasting numeric types
    and converting object columns to category where appropriate.
    
    Args:
        df: pandas DataFrame to optimize.
        
    Returns:
        The optimized DataFrame.
    """
    import pandas as pd
    import numpy as np

    if not HAS_PSUTIL:
        return df

    start_mem = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if pd.api.types.is_integer_dtype(col_type):
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min >= np.iinfo(np.int8).min and c_max <= np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif c_min >= np.iinfo(np.int16).min and c_max <= np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif c_min >= np.iinfo(np.int32).min and c_max <= np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
            else:
                df[col] = df[col].astype(np.int64)
                
        elif pd.api.types.is_float_dtype(col_type):
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min >= np.finfo(np.float32).min and c_max <= np.finfo(np.float32).max:
                df[col] = df[col].astype(np.float32)
            else:
                df[col] = df[col].astype(np.float64)
                
        elif col_type == 'object':
            # Check if converting to category saves memory
            try:
                if df[col].nunique() / len(df[col]) < 0.5: # Heuristic: < 50% unique
                    df[col] = df[col].astype('category')
            except Exception:
                pass
                
    end_mem = df.memory_usage(deep=True).sum() / (1024 * 1024)
    logger.info(f"DataFrame memory optimized from {start_mem:.2f} MB to {end_mem:.2f} MB ({(1 - end_mem/start_mem)*100:.1f}% reduction)")
    return df


def stream_dataframe_chunks(file_path: str, chunksize: int = 10000, **kwargs):
    """
    Generator to stream a CSV file in chunks to avoid loading the entire file into memory.
    
    Args:
        file_path: Path to the CSV file.
        chunksize: Number of rows per chunk.
        **kwargs: Additional arguments for pd.read_csv.
        
    Yields:
        pandas DataFrames containing chunks of the data.
    """
    import pandas as pd
    
    if not HAS_PSUTIL:
        # Fallback if psutil not available, but still chunk
        for chunk in pd.read_csv(file_path, chunksize=chunksize, **kwargs):
            yield chunk
        return

    logger.info(f"Starting to stream chunks from {file_path}")
    for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunksize, **kwargs)):
        current_mem = get_current_memory_mb()
        if current_mem > (MEMORY_LIMIT_GB * 1024 * 0.9):
            logger.warning(f"Memory usage high ({current_mem:.2f} MB) while streaming. Triggering GC.")
            force_gc()
            # If still high after GC, log error but continue
            if get_current_memory_mb() > (MEMORY_LIMIT_GB * 1024):
                logger.error("Memory usage critically high during streaming. Proceed with caution.")
        
        yield chunk
        # Explicitly delete the reference to the previous chunk to help GC
        # (The loop variable 'chunk' is overwritten, but explicit del helps)
        del chunk
        
    logger.info("Finished streaming chunks.")