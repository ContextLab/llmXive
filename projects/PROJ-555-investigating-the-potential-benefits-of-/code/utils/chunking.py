"""
Memory-safe chunking utilities for large data processing.

This module provides utilities to process large datasets in chunks
to ensure peak RAM usage stays below 7GB. It includes dynamic chunk
sizing based on available memory and explicit garbage collection.
"""

import gc
import tracemalloc
from typing import List, Any, Callable, Optional, Iterator
import pandas as pd
import numpy as np

# Target peak memory in GB (7GB as per requirement)
PEAK_MEMORY_LIMIT_GB = 7.0
PEAK_MEMORY_LIMIT_BYTES = PEAK_MEMORY_LIMIT_GB * 1024 ** 3

def estimate_row_size(df: pd.DataFrame) -> int:
    """
    Estimate the memory footprint of a single row in the DataFrame.
    
    Args:
        df: A sample DataFrame to estimate size from
        
    Returns:
        Estimated size in bytes per row
    """
    if len(df) == 0:
        return 1024  # Default fallback
    return df.memory_usage(deep=True).sum() // len(df)

def get_available_memory() -> int:
    """
    Estimate available system memory.
    
    Returns:
        Estimated available memory in bytes.
        Defaults to a safe conservative estimate if detection fails.
    """
    try:
        import psutil
        mem = psutil.virtual_memory()
        # Reserve 2GB for OS and other processes
        return max(0, mem.available - 2 * 1024**3)
    except ImportError:
        # Fallback: assume 4GB available if psutil not installed
        return 4 * 1024 ** 3
    except Exception:
        return 4 * 1024 ** 3

def calculate_safe_chunk_size(df: pd.DataFrame, target_peak_gb: float = PEAK_MEMORY_LIMIT_GB) -> int:
    """
    Calculate a safe chunk size to ensure processing stays within memory limits.
    
    This function estimates the memory required to hold the current chunk,
    plus overhead for processing, ensuring we don't exceed the target limit.
    
    Args:
        df: The full DataFrame being processed
        target_peak_gb: Target peak memory usage in GB
        
    Returns:
        Safe number of rows per chunk
    """
    if len(df) == 0:
        return 10000  # Default small chunk
        
    # Estimate memory per row
    row_size = estimate_row_size(df)
    
    # Calculate available memory for chunks (leave 2GB headroom)
    available_mem = get_available_memory()
    target_mem = min(available_mem, target_peak_gb * 1024 ** 3)
    
    # Reserve 50% for processing overhead
    safe_mem = target_mem * 0.5
    
    # Calculate chunk size
    chunk_size = safe_mem // row_size
    
    # Ensure reasonable bounds
    chunk_size = max(1000, min(chunk_size, len(df)))
    
    return int(chunk_size)

def process_chunked(
    df: pd.DataFrame,
    chunk_size: Optional[int] = None,
    process_func: Optional[Callable[[pd.DataFrame], Any]] = None,
    progress: bool = True,
    target_peak_gb: float = PEAK_MEMORY_LIMIT_GB
) -> List[Any]:
    """
    Process a DataFrame in memory-safe chunks to ensure peak RAM < target_peak_gb.
    
    If chunk_size is not provided, it is automatically calculated based on
    available system memory and the DataFrame's row size to ensure the
    peak memory usage stays below target_peak_gb (default 7GB).
    
    Args:
        df: Input DataFrame
        chunk_size: Number of rows per chunk (optional, auto-calculated if None)
        process_func: Function to apply to each chunk
        progress: Whether to show progress bar
        target_peak_gb: Target peak memory limit in GB
        
    Returns:
        List of results from processing each chunk
        
    Raises:
        MemoryError: If a single row exceeds the memory limit
    """
    if process_func is None:
        raise ValueError("process_func must be provided")
        
    if len(df) == 0:
        return []
        
    # Auto-calculate chunk size if not provided
    if chunk_size is None:
        chunk_size = calculate_safe_chunk_size(df, target_peak_gb)
        
    # Check if single row is too large
    row_size = estimate_row_size(df)
    if row_size > (target_peak_gb * 1024 ** 3 * 0.5):
        raise MemoryError(f"Single row size ({row_size} bytes) exceeds safe limit. "
                        f"Consider processing this data in a different way.")
    
    results = []
    total_rows = len(df)
    num_chunks = (total_rows + chunk_size - 1) // chunk_size
    
    # Start memory tracking
    tracemalloc.start()
    
    try:
        for i in range(0, total_rows, chunk_size):
            current_chunk_idx = i // chunk_size
            
            # Check memory usage before processing chunk
            current, peak = tracemalloc.get_traced_memory()
            if peak > PEAK_MEMORY_LIMIT_BYTES * 0.9:
                # If we're approaching the limit, force GC and wait
                gc.collect()
                current, peak = tracemalloc.get_traced_memory()
                if peak > PEAK_MEMORY_LIMIT_BYTES * 0.95:
                    raise MemoryError(f"Memory limit exceeded during processing. "
                                    f"Peak: {peak / 1024**3:.2f}GB")
            
            chunk = df.iloc[i:i+chunk_size]
            
            # Process the chunk
            result = process_func(chunk)
            results.append(result)
            
            # Explicitly delete chunk reference
            del chunk
            
            # Force garbage collection periodically
            if (current_chunk_idx + 1) % 5 == 0:
                gc.collect()
                current, peak = tracemalloc.get_traced_memory()
                if progress and (current_chunk_idx + 1) % 10 == 0:
                    print(f"Processed {min(i + chunk_size, total_rows)}/{total_rows} rows. "
                        f"Peak memory: {peak / 1024**3:.2f}GB")
            
            # Progress indicator
            if progress:
                progress_pct = ((i + chunk_size) / total_rows) * 100
                print(f"\rProgress: {progress_pct:.1f}% ({min(i + chunk_size, total_rows)}/{total_rows} rows)", end="", flush=True)
    
    finally:
        tracemalloc.stop()
        gc.collect()
        if progress:
            print()  # New line after progress
            
    return results

def split_dataframe(df: pd.DataFrame, chunk_size: Optional[int] = None, 
                   target_peak_gb: float = PEAK_MEMORY_LIMIT_GB) -> Iterator[pd.DataFrame]:
    """
    Generator that yields memory-safe chunks of a DataFrame.
    
    If chunk_size is not provided, it is automatically calculated to ensure
    processing stays within the target memory limit.
    
    Args:
        df: Input DataFrame
        chunk_size: Number of rows per chunk (optional, auto-calculated if None)
        target_peak_gb: Target peak memory limit in GB
        
    Yields:
        DataFrames of size chunk_size (last chunk may be smaller)
        
    Raises:
        MemoryError: If a single row exceeds the memory limit
    """
    if len(df) == 0:
        return
        
    # Auto-calculate chunk size if not provided
    if chunk_size is None:
        chunk_size = calculate_safe_chunk_size(df, target_peak_gb)
        
    # Check if single row is too large
    row_size = estimate_row_size(df)
    if row_size > (target_peak_gb * 1024 ** 3 * 0.5):
        raise MemoryError(f"Single row size ({row_size} bytes) exceeds safe limit.")
    
    total_rows = len(df)
    num_chunks = (total_rows + chunk_size - 1) // chunk_size
    
    tracemalloc.start()
    
    try:
        for i in range(0, total_rows, chunk_size):
            # Memory check before yielding
            current, peak = tracemalloc.get_traced_memory()
            if peak > PEAK_MEMORY_LIMIT_BYTES * 0.9:
                gc.collect()
                current, peak = tracemalloc.get_traced_memory()
                if peak > PEAK_MEMORY_LIMIT_BYTES * 0.95:
                    tracemalloc.stop()
                    raise MemoryError(f"Memory limit exceeded during splitting. "
                                    f"Peak: {peak / 1024**3:.2f}GB")
            
            chunk = df.iloc[i:i+chunk_size]
            yield chunk
            
            # Clean up
            del chunk
            if (i // chunk_size) % 5 == 0:
                gc.collect()
    finally:
        tracemalloc.stop()
        gc.collect()

def validate_memory_constraints(df: pd.DataFrame, target_peak_gb: float = PEAK_MEMORY_LIMIT_GB) -> bool:
    """
    Validate that processing the DataFrame in chunks will stay within memory limits.
    
    Args:
        df: DataFrame to validate
        target_peak_gb: Target peak memory limit in GB
        
    Returns:
        True if safe to process, False otherwise
    """
    if len(df) == 0:
        return True
        
    row_size = estimate_row_size(df)
    available_mem = get_available_memory()
    target_mem = min(available_mem, target_peak_gb * 1024 ** 3)
    
    # Check if single row is too large
    if row_size > (target_mem * 0.5):
        return False
        
    # Calculate minimum chunk size needed
    min_chunk_size = max(1000, row_size // (target_mem * 0.5))
    
    # Check if we can process at least one row
    if min_chunk_size > len(df):
        return False
        
    return True