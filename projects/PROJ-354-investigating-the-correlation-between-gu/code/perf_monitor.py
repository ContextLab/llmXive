"""
Performance monitoring and optimization utilities for the gut microbiome-cognitive correlation study.

This module provides tools to monitor memory usage, estimate dataframe sizes,
calculate safe batch sizes for streaming, and optimize data processing pipelines
to ensure RAM usage stays below 7GB constraints.
"""

import os
import gc
import logging
import sys
import psutil
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Iterator, Union

import pandas as pd
import numpy as np

# Constants for memory management
MAX_RAM_GB = 7.0
MAX_RAM_BYTES = MAX_RAM_GB * 1024**3
SAFETY_MARGIN = 0.8  # Use only 80% of available memory for safety
TARGET_BATCH_MEMORY_GB = 0.5  # Target 500MB per batch
TARGET_BATCH_MEMORY_BYTES = TARGET_BATCH_MEMORY_GB * 1024**3

logger = logging.getLogger(__name__)

def get_current_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage statistics.
    
    Returns:
        Dictionary with 'rss_gb', 'vms_gb', 'percent' keys.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    
    return {
        'rss_gb': mem_info.rss / (1024**3),
        'vms_gb': mem_info.vms / (1024**3),
        'percent': process.memory_percent()
    }

def estimate_dataframe_memory(df: pd.DataFrame) -> float:
    """
    Estimate memory usage of a pandas DataFrame in GB.
    
    Args:
        df: DataFrame to estimate memory for.
        
    Returns:
        Estimated memory usage in GB.
    """
    if df is None:
        return 0.0
    
    # Get memory usage in bytes and convert to GB
    mem_bytes = df.memory_usage(deep=True).sum()
    mem_gb = mem_bytes / (1024**3)
    
    return mem_gb

def estimate_batch_memory(num_rows: int, num_columns: int, dtype_estimate: float = 8.0) -> float:
    """
    Estimate memory usage for a batch of data.
    
    Args:
        num_rows: Number of rows in the batch.
        num_columns: Number of columns in the batch.
        dtype_estimate: Average bytes per cell (default 8 for float64).
        
    Returns:
        Estimated memory usage in GB.
    """
    # Estimate: rows * columns * bytes_per_cell + overhead
    estimated_bytes = num_rows * num_columns * dtype_estimate
    # Add 10% overhead for pandas index and metadata
    estimated_bytes *= 1.1
    
    return estimated_bytes / (1024**3)

def calculate_safe_batch_size(df_sample: Optional[pd.DataFrame] = None, 
                              num_rows_hint: Optional[int] = None,
                              num_columns_hint: Optional[int] = None) -> int:
    """
    Calculate a safe batch size that keeps memory usage under the target threshold.
    
    Args:
        df_sample: Optional sample DataFrame to estimate column types and count.
        num_rows_hint: Hint about total rows (for proportion calculation).
        num_columns_hint: Hint about number of columns.
        
    Returns:
        Safe batch size in number of rows.
    """
    available_memory = MAX_RAM_BYTES * SAFETY_MARGIN
    target_batch_memory = min(TARGET_BATCH_MEMORY_BYTES, available_memory * 0.1)  # Max 10% per batch
    
    if df_sample is not None:
        # Estimate from sample
        sample_memory = estimate_dataframe_memory(df_sample)
        sample_rows = len(df_sample)
        
        if sample_rows > 0:
            memory_per_row = sample_memory / sample_rows
            if memory_per_row > 0:
                batch_size = int(target_batch_memory / memory_per_row)
                return max(batch_size, 100)  # Minimum 100 rows
    
    elif num_rows_hint and num_columns_hint:
        # Estimate from hints
        estimated_memory = estimate_batch_memory(num_rows_hint, num_columns_hint)
        if estimated_memory > 0:
            # Scale down to fit target
            scale_factor = target_batch_memory / estimated_memory
            batch_size = int(num_rows_hint * scale_factor)
            return max(batch_size, 100)
    
    # Default safe batch size
    return 10000

def trigger_memory_cleanup() -> None:
    """
    Trigger garbage collection and memory cleanup.
    """
    gc.collect()
    # Force Python to release memory back to OS
    if hasattr(gc, 'set_threshold'):
        gc.set_threshold(0)
        gc.collect()
        gc.set_threshold(700, 10, 10)

def check_memory_pressure(threshold_percent: float = 80.0) -> Tuple[bool, float]:
    """
    Check if current memory usage is above a threshold.
    
    Args:
        threshold_percent: Percentage of MAX_RAM_GB to trigger warning.
        
    Returns:
        Tuple of (is_pressure, current_percent).
    """
    mem_usage = get_current_memory_usage()
    current_percent = mem_usage['percent']
    
    # Calculate percentage relative to our target limit
    relative_percent = (mem_usage['rss_gb'] / MAX_RAM_GB) * 100
    
    is_pressure = relative_percent > threshold_percent
    
    if is_pressure:
        logger.warning(f"Memory pressure detected: {relative_percent:.1f}% of {MAX_RAM_GB}GB limit")
    
    return is_pressure, relative_percent

def stream_with_memory_monitor(
    loader: Iterator[pd.DataFrame],
    process_fn: callable,
    batch_size_hint: Optional[int] = None,
    cleanup_interval: int = 10
) -> Iterator[pd.DataFrame]:
    """
    Process streaming data with memory monitoring and automatic cleanup.
    
    Args:
        loader: Iterator yielding DataFrames (batches).
        process_fn: Function to apply to each batch.
        batch_size_hint: Optional hint for batch size.
        cleanup_interval: Number of batches between cleanup cycles.
        
    Yields:
        Processed batches.
    """
    batch_count = 0
    
    for batch in loader:
        # Check memory before processing
        is_pressure, _ = check_memory_pressure(threshold_percent=70.0)
        
        if is_pressure:
            logger.info("Triggering memory cleanup due to pressure")
            trigger_memory_cleanup()
            
            # Re-check after cleanup
            is_pressure, _ = check_memory_pressure(threshold_percent=80.0)
            if is_pressure:
                logger.warning("Memory still high after cleanup, proceeding with caution")
        
        # Process the batch
        processed_batch = process_fn(batch)
        
        yield processed_batch
        
        # Cleanup periodically
        batch_count += 1
        if batch_count % cleanup_interval == 0:
            trigger_memory_cleanup()
        
        # Log progress every 100 batches
        if batch_count % 100 == 0:
            mem_info = get_current_memory_usage()
            logger.debug(f"Processed {batch_count} batches. Current memory: {mem_info['rss_gb']:.2f}GB")

def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by downcasting numeric types.
    
    Args:
        df: DataFrame to optimize.
        
    Returns:
        Optimized DataFrame with reduced memory footprint.
    """
    if df is None or df.empty:
        return df
    
    initial_memory = estimate_dataframe_memory(df)
    logger.debug(f"Optimizing DataFrame memory. Initial: {initial_memory:.3f}GB")
    
    # Downcast numeric columns
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    
    for col in numeric_cols:
        if pd.api.types.is_integer_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], downcast='integer')
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], downcast='float')
    
    # Convert object columns to category where appropriate
    object_cols = df.select_dtypes(include=['object']).columns
    for col in object_cols:
        if df[col].nunique() / len(df) < 0.5:  # Only if low cardinality
            df[col] = df[col].astype('category')
    
    optimized_memory = estimate_dataframe_memory(df)
    savings = ((initial_memory - optimized_memory) / initial_memory) * 100 if initial_memory > 0 else 0
    
    logger.debug(f"Optimization complete. Final: {optimized_memory:.3f}GB. Savings: {savings:.1f}%")
    
    return df

def validate_memory_constraints(df: pd.DataFrame, required_operations: List[str]) -> Dict[str, Any]:
    """
    Validate that a DataFrame and planned operations fit within memory constraints.
    
    Args:
        df: DataFrame to validate.
        required_operations: List of operation names that will be performed.
        
    Returns:
        Dictionary with validation results and recommendations.
    """
    df_memory = estimate_dataframe_memory(df)
    total_operations_memory = len(required_operations) * df_memory * 1.5  # Estimate 1.5x per operation
    total_memory = df_memory + total_operations_memory
    
    is_valid = total_memory < (MAX_RAM_BYTES * SAFETY_MARGIN)
    
    result = {
        'df_memory_gb': df_memory,
        'estimated_total_memory_gb': total_memory,
        'max_allowed_gb': MAX_RAM_GB * SAFETY_MARGIN,
        'is_valid': is_valid,
        'operations': required_operations,
        'recommendations': []
    }
    
    if not is_valid:
        result['recommendations'].append("Consider processing in smaller batches")
        result['recommendations'].append("Use streaming processing instead of loading full dataset")
        result['recommendations'].append("Downcast numeric types to reduce memory footprint")
        
        # Calculate recommended batch size
        if len(df) > 0:
            rows_per_gb = len(df) / df_memory if df_memory > 0 else 10000
            recommended_rows = int(rows_per_gb * (MAX_RAM_GB * SAFETY_MARGIN / len(required_operations)))
            result['recommendations'].append(f"Recommended batch size: {recommended_rows:,} rows")
    
    return result

def main():
    """
    Main function to demonstrate and validate memory monitoring capabilities.
    """
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting memory constraint validation")
    
    # Get current memory status
    mem_status = get_current_memory_usage()
    logger.info(f"Current memory usage: {mem_status['rss_gb']:.2f}GB ({mem_status['percent']:.1f}%)")
    
    # Validate constraints
    is_pressure, _ = check_memory_pressure()
    if is_pressure:
        logger.warning("System is under memory pressure")
    else:
        logger.info("Memory usage is within acceptable limits")
    
    # Calculate safe batch size
    batch_size = calculate_safe_batch_size()
    logger.info(f"Recommended safe batch size: {batch_size:,} rows")
    
    logger.info("Memory monitoring validation complete")

if __name__ == "__main__":
    main()
