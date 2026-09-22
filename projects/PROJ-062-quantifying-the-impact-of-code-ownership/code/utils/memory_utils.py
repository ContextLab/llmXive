"""
Memory utilities for the Code Ownership Impact Analysis pipeline.

Provides functions to monitor, optimize, and guard against memory overflows
to ensure the pipeline stays within the 7GB RAM constraint (T042).
"""
import gc
import os
import sys
import logging
import time
from typing import Optional, Callable, Any, List, Dict
import psutil

logger = logging.getLogger(__name__)

# Constants
MEMORY_LIMIT_MB = 7 * 1024  # 7 GB in MB

def get_current_memory_mb() -> float:
    """
    Get the current memory usage of the current process in MB.
    
    Returns:
        float: Current memory usage in MB.
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def check_memory_limit(current_mb: Optional[float] = None, limit_mb: float = MEMORY_LIMIT_MB) -> bool:
    """
    Check if current memory usage is within the specified limit.
    
    Args:
        current_mb: Current memory usage in MB. If None, fetched automatically.
        limit_mb: Memory limit in MB (default 7GB).
        
    Returns:
        bool: True if within limit, False otherwise.
    """
    if current_mb is None:
        current_mb = get_current_memory_mb()
    
    if current_mb > limit_mb:
        logger.warning(f"Memory usage {current_mb:.2f} MB exceeds limit {limit_mb:.2f} MB")
        return False
    return True

def force_gc():
    """Force garbage collection to free up memory."""
    logger.debug("Forcing garbage collection...")
    gc.collect()
    logger.debug("Garbage collection complete.")

def clear_memory():
    """Attempt to clear memory by running GC and clearing internal caches."""
    force_gc()
    # Clear Python's internal free lists
    if hasattr(gc, 'callbacks'):
        # In some Python versions, we can trigger more aggressive cleanup
        pass
    logger.info("Memory cleared.")

def optimize_large_dataframe(df):
    """
    Optimize the memory usage of a pandas DataFrame.
    
    This function downcasts numeric types and converts object columns to categories
    where appropriate to reduce memory footprint.
    
    Args:
        df: pandas DataFrame to optimize.
        
    Returns:
        pandas DataFrame: Optimized DataFrame.
    """
    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        logger.error("pandas and numpy are required for DataFrame optimization.")
        return df

    initial_mem = df.memory_usage(deep=True).sum() / (1024 * 1024)
    logger.debug(f"Initial DataFrame memory: {initial_mem:.2f} MB")

    for col in df.columns:
        col_type = df[col].dtype

        if pd.api.types.is_numeric_dtype(col_type):
            c_min = df[col].min()
            c_max = df[col].max()

            if pd.api.types.is_integer_dtype(col_type):
                if c_min >= np.iinfo(np.int8).min and c_max <= np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min >= np.iinfo(np.int16).min and c_max <= np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min >= np.iinfo(np.int32).min and c_max <= np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                else:
                    df[col] = df[col].astype(np.int64)
            else:
                if c_min >= np.finfo(np.float16).min and c_max <= np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min >= np.finfo(np.float32).min and c_max <= np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
        elif pd.api.types.is_object_dtype(col_type):
            # Try to convert to category if unique values are low
            num_unique = df[col].nunique()
            num_total = len(df[col])
            if num_unique / num_total < 0.5 and num_unique > 0:
                df[col] = df[col].astype('category')

    final_mem = df.memory_usage(deep=True).sum() / (1024 * 1024)
    logger.debug(f"Optimized DataFrame memory: {final_mem:.2f} MB (Saved {initial_mem - final_mem:.2f} MB)")
    return df

def memory_limit_guard(func: Callable) -> Callable:
    """
    Decorator to enforce memory limits on a function.
    
    If the function exceeds the memory limit, it will log a warning and force GC.
    If the memory remains too high after GC, it raises a MemoryError.
    
    Args:
        func: Function to wrap.
        
    Returns:
        Callable: Wrapped function.
    """
    def wrapper(*args, **kwargs):
        start_mem = get_current_memory_mb()
        try:
            return func(*args, **kwargs)
        finally:
            end_mem = get_current_memory_mb()
            if end_mem - start_mem > MEMORY_LIMIT_MB * 0.5:
                logger.warning(f"Function {func.__name__} caused a large memory spike: {end_mem - start_mem:.2f} MB")
                force_gc()
                if not check_memory_limit():
                    raise MemoryError(f"Memory limit exceeded after function {func.__name__}")
    return wrapper

def process_repository_batch(repos: List[str], process_func: Callable) -> Dict[str, Any]:
    """
    Process a batch of repositories with memory monitoring.
    
    Args:
        repos: List of repository identifiers.
        process_func: Function to process a single repository.
        
    Returns:
        Dict: Results of the batch processing.
    """
    results = {}
    for repo in repos:
        if not check_memory_limit():
            logger.error(f"Memory limit reached before processing {repo}. Stopping batch.")
            break
        
        try:
            logger.info(f"Processing {repo}...")
            results[repo] = process_func(repo)
            # Force GC after each repo to prevent accumulation
            force_gc()
        except Exception as e:
            logger.error(f"Error processing {repo}: {e}")
            results[repo] = {"error": str(e)}
    
    return results

def process_single_repository(repo: str, process_func: Callable) -> Any:
    """
    Process a single repository with memory monitoring.
    
    Args:
        repo: Repository identifier.
        process_func: Function to process the repository.
        
    Returns:
        Any: Result of the processing function.
    """
    if not check_memory_limit():
        raise MemoryError(f"Memory limit exceeded before processing {repo}")
    
    start_mem = get_current_memory_mb()
    try:
        return process_func(repo)
    finally:
        end_mem = get_current_memory_mb()
        logger.debug(f"Processed {repo}. Memory delta: {end_mem - start_mem:.2f} MB")
        force_gc()

def get_peak_memory_mb() -> float:
    """
    Get the peak memory usage of the current process.
    
    Returns:
        float: Peak memory usage in MB.
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024.0  # Convert KB to MB on Linux
    except AttributeError:
        # Fallback for Windows
        process = psutil.Process(os.getpid())
        return process.memory_info().peak_wset / (1024 * 1024)
