"""
Memory monitoring and dynamic batch sizing utilities.
"""
from __future__ import annotations

import os
import sys
from typing import Optional, Tuple
import psutil
from code.logging_config import get_logger

logger = get_logger(__name__)

def get_available_memory() -> float:
    """
    Get available system memory in bytes.
    """
    try:
        mem = psutil.virtual_memory()
        available = mem.available
        logger.log("get_available_memory", available_bytes=available, total_bytes=mem.total)
        return float(available)
    except Exception as e:
        logger.log("get_available_memory_error", error=str(e))
        # Fallback: assume 4GB available
        return 4.0 * 1024**3

def estimate_memory_usage(n_rows: int, n_cols: int, dtype_size: int = 8) -> float:
    """
    Estimate memory usage for a matrix of given dimensions.
    dtype_size: bytes per element (default 8 for float64)
    """
    # Base matrix size
    matrix_size = n_rows * n_cols * dtype_size
    # Add 50% overhead for pandas/DataFrame operations
    estimated = matrix_size * 1.5
    logger.log("estimate_memory_usage", 
               n_rows=n_rows, 
               n_cols=n_cols, 
               dtype_size=dtype_size, 
               estimated_bytes=estimated)
    return estimated

def calculate_batch_size(n_rows: int, 
                        n_cols: int, 
                        max_memory_fraction: float = 0.8) -> int:
    """
    Calculate optimal batch size for matrix operations.
    
    Args:
        n_rows: Total number of rows to process
        n_cols: Number of columns per row
        max_memory_fraction: Maximum fraction of available memory to use (0.0-1.0)
    
    Returns:
        Optimal batch size (number of rows per batch)
    """
    available_mem = get_available_memory()
    safe_limit = available_mem * max_memory_fraction
    
    # Memory per row
    mem_per_row = estimate_memory_usage(1, n_cols)
    
    if mem_per_row == 0:
        return n_rows
    
    # Calculate batch size
    batch_size = int(safe_limit / mem_per_row)
    
    # Ensure batch size is at least 1 and at most n_rows
    batch_size = max(1, min(batch_size, n_rows))
    
    logger.log("calculate_batch_size", 
               available_mem=available_mem, 
               safe_limit=safe_limit, 
               mem_per_row=mem_per_row, 
               calculated_batch_size=batch_size, 
               total_rows=n_rows)
    return batch_size

def verify_batching_logic(n_rows: int, n_cols: int, max_memory_gb: float = 7.0) -> Tuple[int, bool]:
    """
    Verify that calculated batch size respects memory constraints.
    
    Returns:
        Tuple of (batch_size, is_valid)
    """
    available_mem = get_available_memory()
    limit_bytes = max_memory_gb * 1024**3
    
    batch_size = calculate_batch_size(n_rows, n_cols)
    
    # Verify batch fits in memory
    batch_mem = estimate_memory_usage(batch_size, n_cols)
    is_valid = batch_mem < limit_bytes
    
    logger.log("verify_batching_logic", 
               batch_size=batch_size, 
               batch_mem_bytes=batch_mem, 
               limit_bytes=limit_bytes, 
               is_valid=is_valid)
    
    return batch_size, is_valid