"""
Memory optimization utilities for the alloy prediction pipeline.

This module provides functions to monitor memory usage and optimize
data structures to stay within the 4GB peak memory target.
"""
import gc
import logging
import tracemalloc
from typing import Any, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
import pandas as pd

from config import get_config
from logging_config import get_logger

# Maximum allowed memory in bytes (4GB)
MAX_MEMORY_BYTES = 4 * 1024 * 1024 * 1024
MEMORY_WARNING_THRESHOLD = 0.8  # Warn at 80% of limit
MEMORY_CRITICAL_THRESHOLD = 0.95  # Critical at 95% of limit

logger = get_logger(__name__)

def get_current_memory_usage() -> Tuple[float, float]:
    """
    Get current memory usage in bytes.
    
    Returns:
        Tuple of (current_bytes, peak_bytes)
    """
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    
    current, peak = tracemalloc.get_traced_memory()
    return current, peak

def check_memory_usage(warn_only: bool = True) -> bool:
    """
    Check if current memory usage exceeds thresholds.
    
    Args:
        warn_only: If True, only log warnings. If False, raise errors for critical.
        
    Returns:
        True if memory usage is acceptable, False otherwise.
        
    Raises:
        MemoryError: If memory usage exceeds critical threshold and warn_only is False.
    """
    current, peak = get_current_memory_usage()
    
    current_ratio = current / MAX_MEMORY_BYTES
    peak_ratio = peak / MAX_MEMORY_BYTES
    
    if peak_ratio > MEMORY_CRITICAL_THRESHOLD and not warn_only:
        error_msg = (
            f"CRITICAL: Peak memory usage {peak_ratio:.1%} ({peak / 1024**3:.2f}GB) "
            f"exceeds critical threshold {MEMORY_CRITICAL_THRESHOLD:.0%}. "
            f"Current usage: {current_ratio:.1%} ({current / 1024**3:.2f}GB)."
        )
        logger.error(error_msg)
        raise MemoryError(error_msg)
        
    if peak_ratio > MEMORY_WARNING_THRESHOLD:
        warning_msg = (
            f"WARNING: Peak memory usage {peak_ratio:.1%} ({peak / 1024**3:.2f}GB) "
            f"exceeds warning threshold {MEMORY_WARNING_THRESHOLD:.0%}. "
            f"Current usage: {current_ratio:.1%} ({current / 1024**3:.2f}GB)."
        )
        logger.warning(warning_msg)
        
    return True

def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize memory usage of a pandas DataFrame.
    
    This function:
    - Downcasts numeric columns to smallest possible dtype
    - Converts object columns to category where appropriate
    - Removes unnecessary index if not needed
    
    Args:
        df: Input DataFrame
        
    Returns:
        Optimized DataFrame with reduced memory usage
    """
    initial_memory = df.memory_usage(deep=True).sum()
    
    # Select numeric columns for downcasting
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    
    for col in numeric_cols:
        col_min = df[col].min()
        col_max = df[col].max()
        
        if pd.api.types.is_integer_dtype(df[col]):
            if col_min >= np.iinfo(np.int8).min and col_max <= np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif col_min >= np.iinfo(np.int16).min and col_max <= np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif col_min >= np.iinfo(np.int32).min and col_max <= np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
        elif pd.api.types.is_float_dtype(df[col]):
            # Check if float32 is sufficient
            if col_min >= np.finfo(np.float32).min and col_max <= np.finfo(np.float32).max:
                df[col] = df[col].astype(np.float32)
    
    # Convert object columns to category if they have low cardinality
    object_cols = df.select_dtypes(include=['object']).columns
    for col in object_cols:
        if df[col].nunique() / len(df[col]) < 0.5:  # Less than 50% unique values
            df[col] = df[col].astype('category')
    
    final_memory = df.memory_usage(deep=True).sum()
    savings = initial_memory - final_memory
    savings_pct = (savings / initial_memory * 100) if initial_memory > 0 else 0
    
    logger.info(
        f"Memory optimization: {initial_memory / 1024**2:.2f}MB -> "
        f"{final_memory / 1024**2:.2f}MB (saved {savings / 1024**2:.2f}MB, {savings_pct:.1f}%)"
    )
    
    return df

def chunked_dataframe_loader(
    filepath: Path,
    chunksize: int = 10000,
    optimize: bool = True
):
    """
    Generator that loads a CSV file in chunks to manage memory.
    
    Args:
        filepath: Path to the CSV file
        chunksize: Number of rows per chunk
        optimize: Whether to apply memory optimization to each chunk
        
    Yields:
        DataFrames of specified chunk size
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
        
    for chunk in pd.read_csv(filepath, chunksize=chunksize):
        if optimize:
            chunk = optimize_dataframe_memory(chunk)
        yield chunk
        # Force garbage collection after each chunk
        gc.collect()

def process_large_dataset_with_memory_check(
    processor_func,
    input_path: Path,
    output_path: Path,
    chunksize: int = 10000,
    optimize: bool = True
):
    """
    Process a large dataset in chunks while monitoring memory usage.
    
    Args:
        processor_func: Function that processes a chunk (chunk -> processed_chunk)
        input_path: Path to input CSV
        output_path: Path to output CSV
        chunksize: Number of rows per chunk
        optimize: Whether to optimize memory of chunks
        
    Raises:
        MemoryError: If memory usage exceeds critical threshold
    """
    logger.info(f"Starting memory-efficient processing of {input_path}")
    
    # Initialize output file
    first_chunk = True
    
    for chunk_idx, chunk in enumerate(
        chunked_dataframe_loader(input_path, chunksize, optimize)
    ):
        # Check memory before processing
        check_memory_usage(warn_only=False)
        
        # Process the chunk
        processed_chunk = processor_func(chunk)
        
        # Check memory after processing
        check_memory_usage(warn_only=True)
        
        # Write to output
        mode = 'w' if first_chunk else 'a'
        header = first_chunk
        processed_chunk.to_csv(
            output_path, 
            mode=mode, 
            header=header, 
            index=False
        )
        
        if first_chunk:
            first_chunk = False
            logger.info(f"Processed chunk {chunk_idx + 1}, writing to {output_path}")
        
        # Force garbage collection
        gc.collect()
        
        # Check memory again after cleanup
        check_memory_usage(warn_only=True)
    
    logger.info(f"Completed processing. Output written to {output_path}")

def clear_unused_memory():
    """
    Force garbage collection and clear unused memory.
    """
    gc.collect()
    logger.debug("Memory garbage collection completed")

def get_memory_profile_summary() -> Dict[str, Any]:
    """
    Get a summary of memory profile.
    
    Returns:
        Dictionary with memory statistics
    """
    current, peak = get_current_memory_usage()
    
    return {
        "current_bytes": current,
        "current_gb": current / 1024**3,
        "peak_bytes": peak,
        "peak_gb": peak / 1024**3,
        "max_allowed_bytes": MAX_MEMORY_BYTES,
        "max_allowed_gb": MAX_MEMORY_BYTES / 1024**3,
        "current_usage_pct": (current / MAX_MEMORY_BYTES) * 100,
        "peak_usage_pct": (peak / MAX_MEMORY_BYTES) * 100,
        "within_limit": peak <= MAX_MEMORY_BYTES
    }

def main():
    """
    Main function to demonstrate memory optimization utilities.
    """
    config = get_config()
    setup_logging(config)
    
    logger.info("Memory Optimization Utilities Demo")
    logger.info(f"Max allowed memory: {MAX_MEMORY_BYTES / 1024**3:.2f}GB")
    
    # Example: Create a large DataFrame and optimize it
    logger.info("Creating sample DataFrame...")
    df = pd.DataFrame({
        'int_col': range(1000000),
        'float_col': np.random.random(1000000),
        'object_col': [f'item_{i % 1000}' for i in range(1000000)]
    })
    
    logger.info(f"Original memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f}MB")
    
    optimized_df = optimize_dataframe_memory(df)
    logger.info(f"Optimized memory usage: {optimized_df.memory_usage(deep=True).sum() / 1024**2:.2f}MB")
    
    # Check memory
    check_memory_usage(warn_only=False)
    
    logger.info("Memory optimization demo completed successfully")
