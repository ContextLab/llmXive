"""
Memory monitoring and optimization utilities for the epigenetic drift pipeline.

This module provides tools to ensure the pipeline stays within the 2GB RAM constraint
specified in the project requirements.
"""

import gc
import logging
import os
import sys
import tracemalloc
from pathlib import Path
from typing import Optional, Callable, Any, Dict

import numpy as np
import pandas as pd

from config import get_env_int

# Configure logging
logger = logging.getLogger(__name__)

# Memory limit in bytes (2GB)
MEMORY_LIMIT_BYTES = get_env_int("MEMORY_LIMIT_BYTES", 2 * 1024 * 1024 * 1024)
MEMORY_WARNING_THRESHOLD = get_env_int("MEMORY_WARNING_THRESHOLD", int(1.8 * 1024 * 1024 * 1024))

def get_memory_usage() -> int:
    """
    Get current memory usage in bytes.
    
    Returns:
        Current memory usage in bytes, or 0 if measurement fails.
    """
    if sys.platform == "linux":
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        # VmRSS is in kB
                        return int(line.split()[1]) * 1024
        except Exception as e:
            logger.warning(f"Could not read /proc/self/status: {e}")
    
    # Fallback: use tracemalloc if running
    if tracemalloc.is_tracing():
        current, _ = tracemalloc.get_traced_memory()
        return current
    
    return 0

def check_memory_usage() -> bool:
    """
    Check if current memory usage is within limits.
    
    Returns:
        True if within limits, False if exceeded.
    """
    current_usage = get_memory_usage()
    
    if current_usage >= MEMORY_LIMIT_BYTES:
        logger.error(f"Memory limit exceeded: {current_usage / (1024**3):.2f} GB >= {MEMORY_LIMIT_BYTES / (1024**3):.2f} GB")
        return False
    
    if current_usage >= MEMORY_WARNING_THRESHOLD:
        logger.warning(f"Memory usage high: {current_usage / (1024**3):.2f} GB")
    
    return True

def cleanup_memory() -> None:
    """
    Force garbage collection and clear numpy/pandas caches.
    """
    gc.collect()
    
    # Clear numpy caches if available
    if hasattr(np, "clear_cache"):
        np.clear_cache()
    
    # Clear pandas caches
    if hasattr(pd, "options") and hasattr(pd.options, "mode"):
        # Force pandas to release some internal caches
        pass
    
    logger.debug("Memory cleanup completed")

def chunked_iter(df: pd.DataFrame, chunk_size: int = 10000):
    """
    Iterate over a DataFrame in chunks to reduce memory pressure.
    
    Args:
        df: DataFrame to iterate over
        chunk_size: Number of rows per chunk
    
    Yields:
        DataFrame chunks
    """
    total_rows = len(df)
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        chunk = df.iloc[start:end]
        yield chunk
        
        # Periodic cleanup
        if (start // chunk_size) % 10 == 0:
            cleanup_memory()
            if not check_memory_usage():
                raise MemoryError("Memory limit exceeded during chunked iteration")

def process_in_chunks(
    data: pd.DataFrame,
    processor: Callable[[pd.DataFrame], pd.DataFrame],
    chunk_size: int = 10000
) -> pd.DataFrame:
    """
    Process a large DataFrame in chunks to stay within memory limits.
    
    Args:
        data: Input DataFrame
        processor: Function to apply to each chunk
        chunk_size: Number of rows per chunk
    
    Returns:
        Processed DataFrame (concatenated chunks)
    """
    results = []
    
    for chunk in chunked_iter(data, chunk_size):
        processed_chunk = processor(chunk)
        results.append(processed_chunk)
        cleanup_memory()
    
    if not results:
        return pd.DataFrame()
    
    return pd.concat(results, ignore_index=True)

def reduce_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by downcasting numeric types.
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with optimized memory usage
    """
    df_optimized = df.copy()
    
    for col in df_optimized.columns:
        col_type = df_optimized[col].dtype
        
        if pd.api.types.is_integer_dtype(col_type):
            min_val = df_optimized[col].min()
            max_val = df_optimized[col].max()
            
            if min_val >= 0:
                if max_val < 256:
                    df_optimized[col] = df_optimized[col].astype("uint8")
                elif max_val < 65536:
                    df_optimized[col] = df_optimized[col].astype("uint16")
                elif max_val < 4294967296:
                    df_optimized[col] = df_optimized[col].astype("uint32")
            else:
                if min_val > -128 and max_val < 128:
                    df_optimized[col] = df_optimized[col].astype("int8")
                elif min_val > -32768 and max_val < 32768:
                    df_optimized[col] = df_optimized[col].astype("int16")
                elif min_val > -2147483648 and max_val < 2147483648:
                    df_optimized[col] = df_optimized[col].astype("int32")
        
        elif pd.api.types.is_float_dtype(col_type):
            if df_optimized[col].isna().all():
                continue
            
            min_val = df_optimized[col].min()
            max_val = df_optimized[col].max()
            
            if min_val >= -3.4e38 and max_val <= 3.4e38:
                df_optimized[col] = df_optimized[col].astype("float32")
    
    return df_optimized

def memory_profile(func: Callable) -> Callable:
    """
    Decorator to profile memory usage of a function.
    
    Args:
        func: Function to profile
    
    Returns:
        Wrapped function with memory profiling
    """
    def wrapper(*args, **kwargs) -> Any:
        gc.collect()
        start_mem = get_memory_usage()
        tracemalloc.start()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            end_mem = get_memory_usage()
            mem_diff = (end_mem - start_mem) / (1024 ** 2)
            peak_mem = peak / (1024 ** 2)
            
            logger.info(
                f"Memory profile for {func.__name__}: "
                f"Delta: {mem_diff:.2f} MB, Peak: {peak_mem:.2f} MB"
            )
            
            if not check_memory_usage():
                raise MemoryError(f"Memory limit exceeded in {func.__name__}")
    
    return wrapper

def enforce_memory_limit(func: Callable) -> Callable:
    """
    Decorator to enforce memory limits during function execution.
    
    Args:
        func: Function to wrap
    
    Returns:
        Wrapped function with memory enforcement
    """
    def wrapper(*args, **kwargs) -> Any:
        if not check_memory_usage():
            raise MemoryError("Memory limit already exceeded before function execution")
        
        gc.collect()
        tracemalloc.start()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            cleanup_memory()
            if not check_memory_usage():
                raise MemoryError("Memory limit exceeded during function execution")
    
    return wrapper

def main() -> None:
    """
    Run memory monitoring demonstration and tests.
    """
    logger.info("Memory monitoring module initialized")
    logger.info(f"Memory limit: {MEMORY_LIMIT_BYTES / (1024**3):.2f} GB")
    
    # Test memory usage
    current = get_memory_usage()
    logger.info(f"Current memory usage: {current / (1024**2):.2f} MB")
    
    # Test cleanup
    cleanup_memory()
    
    # Test memory profile decorator
    @memory_profile
    def test_function():
        data = pd.DataFrame(np.random.rand(1000000, 10))
        return data.mean()
    
    result = test_function()
    logger.info(f"Test function result: {result}")
    
    logger.info("Memory monitoring module tests completed")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main()