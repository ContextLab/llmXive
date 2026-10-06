"""
Memory monitoring and optimization utilities for the genomic analysis pipeline.

This module provides tools to monitor memory usage, manage garbage collection,
and implement streaming/chunked processing to ensure memory usage stays below
the 6GB threshold defined in the project constraints.
"""
import os
import gc
import psutil
import logging
import pandas as pd
import numpy as np
from typing import Generator, Optional, List, Dict, Any, Callable
from pathlib import Path
from contextlib import contextmanager

from src.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

# Memory limit in MB (6GB as per task requirement)
MEMORY_LIMIT_MB: int = 6000
MEMORY_WARNING_THRESHOLD_MB: int = 5000
CHUNK_SIZE_DEFAULT: int = 10000  # Default number of rows per chunk for streaming

def get_current_memory_mb() -> float:
    """
    Get the current memory usage of the current process in megabytes.
    
    Returns:
        float: Memory usage in MB
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def check_memory_usage(threshold_mb: Optional[int] = None) -> bool:
    """
    Check if current memory usage is within acceptable limits.
    
    Args:
        threshold_mb: Optional custom threshold in MB. Defaults to MEMORY_WARNING_THRESHOLD_MB.
        
    Returns:
        bool: True if usage is below threshold, False otherwise.
    """
    threshold = threshold_mb or MEMORY_WARNING_THRESHOLD_MB
    current = get_current_memory_mb()
    if current > threshold:
        logger.warning(f"Memory usage ({current:.2f} MB) exceeds threshold ({threshold} MB)")
        return False
    return True

def force_gc() -> float:
    """
    Force garbage collection and return the memory freed.
    
    Returns:
        float: Memory usage in MB after garbage collection.
    """
    initial = get_current_memory_mb()
    gc.collect()
    final = get_current_memory_mb()
    freed = initial - final
    if freed > 0:
        logger.info(f"Garbage collection freed {freed:.2f} MB")
    return final

@contextmanager
def memory_limited_context(threshold_mb: Optional[int] = None):
    """
    Context manager that monitors memory usage and forces GC if threshold is exceeded.
    
    Args:
        threshold_mb: Optional custom threshold in MB. Defaults to MEMORY_LIMIT_MB.
        
    Raises:
        MemoryError: If memory usage exceeds the hard limit even after GC.
    """
    threshold = threshold_mb or MEMORY_LIMIT_MB
    try:
        yield
        # Check memory after operation
        if not check_memory_usage(threshold):
            logger.warning("Memory threshold exceeded, attempting garbage collection")
            current = force_gc()
            if current > threshold:
                raise MemoryError(
                    f"Memory usage ({current:.2f} MB) exceeds hard limit ({threshold} MB) "
                    "even after garbage collection. Consider processing data in smaller chunks."
                )
    except MemoryError:
        raise
    except Exception as e:
        logger.error(f"Error in memory-limited context: {e}")
        raise

def stream_dataframe(
    df: pd.DataFrame,
    chunk_size: int = CHUNK_SIZE_DEFAULT,
    columns: Optional[List[str]] = None
) -> Generator[pd.DataFrame, None, None]:
    """
    Stream a DataFrame in chunks to reduce memory pressure.
    
    This is useful for processing large genomic datasets that cannot fit
    entirely in memory.
    
    Args:
        df: The DataFrame to stream.
        chunk_size: Number of rows per chunk.
        columns: Optional list of columns to include in each chunk.
                
    Yields:
        pd.DataFrame: A chunk of the original DataFrame.
    """
    total_rows = len(df)
    if columns:
        df = df[columns]
        
    for start_idx in range(0, total_rows, chunk_size):
        end_idx = min(start_idx + chunk_size, total_rows)
        chunk = df.iloc[start_idx:end_idx]
        yield chunk
        
        # Force GC after each chunk if memory is high
        if get_current_memory_mb() > MEMORY_WARNING_THRESHOLD_MB:
            force_gc()

def optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize memory usage of a DataFrame by downcasting numeric types.
    
    Args:
        df: The DataFrame to optimize.
        
    Returns:
        pd.DataFrame: The same DataFrame with optimized dtypes.
    """
    initial_memory = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
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
                
        elif pd.api.types.is_categorical_dtype(col_type):
            df[col] = df[col].astype('category')
            
    final_memory = df.memory_usage(deep=True).sum() / (1024 * 1024)
    saved = initial_memory - final_memory
    if saved > 0:
        logger.info(f"Optimized DataFrame memory usage: {initial_memory:.2f} MB -> {final_memory:.2f} MB (saved {saved:.2f} MB)")
        
    return df

def process_large_dataset_in_chunks(
    data_loader: Callable[[int, int], pd.DataFrame],
    total_rows: int,
    chunk_size: int = CHUNK_SIZE_DEFAULT,
    process_func: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
    aggregate_func: Optional[Callable[[List[pd.DataFrame]], Any]] = None
) -> Any:
    """
    Process a large dataset in chunks to stay within memory limits.
    
    Args:
        data_loader: Function that loads a chunk of data given start and end indices.
        total_rows: Total number of rows in the dataset.
        chunk_size: Number of rows per chunk.
        process_func: Optional function to apply to each chunk.
        aggregate_func: Optional function to aggregate results from all chunks.
        
    Returns:
        Any: Aggregated results or None if no aggregate_func provided.
    """
    results = []
    
    for start_idx in range(0, total_rows, chunk_size):
        end_idx = min(start_idx + chunk_size, total_rows)
        
        logger.info(f"Processing chunk: rows {start_idx} to {end_idx}")
        
        # Load chunk
        chunk = data_loader(start_idx, end_idx)
        
        # Process if function provided
        if process_func:
            chunk = process_func(chunk)
            
        results.append(chunk)
        
        # Check memory and force GC if needed
        if get_current_memory_mb() > MEMORY_WARNING_THRESHOLD_MB:
            logger.warning("High memory usage detected, forcing garbage collection")
            force_gc()
            
        # Early cleanup if no aggregation needed
        if not aggregate_func:
            del chunk
            gc.collect()
    
    # Aggregate results if function provided
    if aggregate_func:
        return aggregate_func(results)
        
    return None

def get_memory_profile() -> Dict[str, Any]:
    """
    Get a detailed memory profile of the current process.
    
    Returns:
        Dict containing memory usage statistics.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    
    return {
        'rss_mb': mem_info.rss / (1024 * 1024),
        'vms_mb': mem_info.vms / (1024 * 1024),
        'percent': process.memory_percent(),
        'num_threads': process.num_threads(),
        'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0
    }

def ensure_memory_safe_operation(
    operation: Callable[[], Any],
    max_memory_mb: int = MEMORY_LIMIT_MB
) -> Any:
    """
    Execute an operation with memory safety checks.
    
    Args:
        operation: The operation to execute.
        max_memory_mb: Maximum allowed memory usage in MB.
        
    Returns:
        Any: The result of the operation.
        
    Raises:
        MemoryError: If the operation would exceed memory limits.
    """
    initial_memory = get_current_memory_mb()
    
    if initial_memory > max_memory_mb:
        raise MemoryError(
            f"Cannot execute operation: current memory ({initial_memory:.2f} MB) "
            f"already exceeds limit ({max_memory_mb} MB)"
        )
        
    try:
        result = operation()
        final_memory = get_current_memory_mb()
        
        if final_memory > max_memory_mb:
            logger.warning(
                f"Operation completed but memory ({final_memory:.2f} MB) "
                f"exceeds limit ({max_memory_mb} MB). Consider refactoring."
            )
            
        return result
        
    except MemoryError:
        raise
    except Exception as e:
        logger.error(f"Error during memory-safe operation: {e}")
        raise

def cleanup_unused_variables(variable_names: List[str], local_scope: Optional[Dict[str, Any]] = None) -> float:
    """
    Explicitly delete variables from scope to free memory.
    
    Args:
        variable_names: List of variable names to delete.
        local_scope: Optional local scope dictionary. Defaults to current locals().
        
    Returns:
        float: Memory usage after cleanup.
    """
    scope = local_scope or locals()
    for name in variable_names:
        if name in scope:
            del scope[name]
            
    return force_gc()