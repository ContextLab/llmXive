"""
Optimization utilities for pipeline performance improvement.

This module provides utility functions and decorators to optimize
memory and CPU usage in the pipeline.
"""

import os
import sys
import time
import logging
import resource
from functools import wraps
from typing import Callable, Any, Optional
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

def set_thread_pool_size(max_threads: int = 2):
    """
    Set the number of threads for parallel operations.
    
    This is critical for controlling CPU usage on multi-core systems.
    """
    os.environ["OMP_NUM_THREADS"] = str(max_threads)
    os.environ["OPENBLAS_NUM_THREADS"] = str(max_threads)
    os.environ["MKL_NUM_THREADS"] = str(max_threads)
    os.environ["VECLIB_MAXIMUM_THREADS"] = str(max_threads)
    os.environ["NUMEXPR_NUM_THREADS"] = str(max_threads)
    
    logger.info(f"Thread pool size set to {max_threads}")

def memory_monitor(threshold_mb: float = 4000):
    """
    Context manager to monitor memory usage.
    
    Raises MemoryError if usage exceeds threshold.
    """
    class MemoryMonitor:
        def __enter__(self):
            self.start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # MB on Linux
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
            delta = end_mem - self.start_mem
            
            if end_mem > threshold_mb:
                logger.warning(f"Memory usage exceeded threshold: {end_mem:.2f}MB > {threshold_mb}MB")
                if exc_type is None:
                    raise MemoryError(f"Memory usage exceeded {threshold_mb}MB")
            
            logger.debug(f"Memory delta: {delta:.2f}MB, Peak: {end_mem:.2f}MB")
            return False
    
    return MemoryMonitor()

def chunked_dataframe(df: pd.DataFrame, chunk_size: int = 1000):
    """
    Generator that yields chunks of a DataFrame.
    
    Useful for processing large datasets without loading everything into memory.
    """
    for i in range(0, len(df), chunk_size):
        yield df.iloc[i:i + chunk_size]

def cache_result(func: Callable):
    """
    Simple decorator to cache function results.
    
    Useful for expensive operations that might be called multiple times.
    """
    cache = {}
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create a simple cache key
        key = str(args) + str(sorted(kwargs.items()))
        
        if key in cache:
            logger.debug(f"Cache hit for {func.__name__}")
            return cache[key]
        
        logger.debug(f"Cache miss for {func.__name__}")
        result = func(*args, **kwargs)
        cache[key] = result
        
        return result
    
    return wrapper

def optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by downcasting numeric types.
    
    Returns a new DataFrame with optimized dtypes.
    """
    original_size = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type == "object":
            # Convert object columns to category if low cardinality
            if df[col].nunique() / len(df) < 0.5:
                df[col] = df[col].astype("category")
        
        elif col_type in ["int64", "float64"]:
            # Downcast integers
            if pd.api.types.is_integer_dtype(df[col]):
                c_min = df[col].min()
                c_max = df[col].max()
                
                if c_min >= np.iinfo(np.int8).min and c_max <= np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min >= np.iinfo(np.int16).min and c_max <= np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min >= np.iinfo(np.int32).min and c_max <= np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
            
            # Downcast floats
            elif pd.api.types.is_float_dtype(df[col]):
                c_min = df[col].min()
                c_max = df[col].max()
                
                if c_min >= np.finfo(np.float32).min and c_max <= np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
    
    optimized_size = df.memory_usage(deep=True).sum() / (1024 * 1024)
    savings = ((original_size - optimized_size) / original_size) * 100
    
    logger.info(f"DataFrame memory optimization: {original_size:.2f}MB -> {optimized_size:.2f}MB ({savings:.1f}% savings)")
    
    return df

def save_to_parquet(df: pd.DataFrame, path: Path):
    """
    Save DataFrame to Parquet format for better compression and faster I/O.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")
    logger.info(f"Saved DataFrame to {path}")

def load_from_parquet(path: Path) -> pd.DataFrame:
    """
    Load DataFrame from Parquet format.
    """
    df = pd.read_parquet(path)
    logger.info(f"Loaded DataFrame from {path}")
    return df

def batch_process(items: list, process_func: Callable, batch_size: int = 100):
    """
    Process items in batches to manage memory usage.
    """
    results = []
    total = len(items)
    
    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        logger.debug(f"Processing batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
        
        batch_results = [process_func(item) for item in batch]
        results.extend(batch_results)
        
        # Force garbage collection every few batches
        if (i // batch_size) % 5 == 0:
            import gc
            gc.collect()
    
    return results

def profile_function(func: Callable) -> Callable:
    """
    Decorator to profile function execution time and memory.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        
        duration = end_time - start_time
        mem_delta = end_mem - start_mem
        
        logger.info(
            f"{func.__name__}: {duration:.2f}s, "
            f"Memory: {mem_delta:.2f}MB (Peak: {end_mem:.2f}MB)"
        )
        
        return result
    
    return wrapper
