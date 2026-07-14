from __future__ import annotations

import os
import sys
from typing import Optional, Tuple
import psutil
from code.logging_config import get_logger

logger = get_logger(__name__)

def get_available_memory() -> int:
    """
    Get available system memory in bytes.
    Uses psutil for cross-platform compatibility.
    """
    try:
        mem = psutil.virtual_memory()
        available = mem.available
        logger.log("memory_check", available_bytes=available, total_bytes=mem.total)
        return available
    except Exception as e:
        logger.log("memory_check_failed", error=str(e))
        # Fallback to a conservative estimate if psutil fails
        return 2 * 1024 * 1024 * 1024  # 2GB fallback

def estimate_memory_usage(rows: int, columns: int, dtype_size: int = 8) -> int:
    """
    Estimate memory usage for a matrix of given dimensions.
    
    Args:
        rows: Number of rows
        columns: Number of columns
        dtype_size: Size of data type in bytes (default 8 for float64)
        
    Returns:
        Estimated memory in bytes
    """
    return rows * columns * dtype_size

def calculate_batch_size(total_rows: int, max_memory_fraction: float = 0.8) -> int:
    """
    Calculate optimal batch size to respect memory constraints.
    
    Args:
        total_rows: Total number of rows to process
        max_memory_fraction: Fraction of available memory to use (0.0 to 1.0)
        
    Returns:
        Optimal batch size (number of rows)
    """
    available_mem = get_available_memory()
    safe_mem = int(available_mem * max_memory_fraction)
    
    # Heuristic: Estimate memory per row for typical analysis operations
    # Assume we need space for:
    # - Input data (float64)
    # - Intermediate matrices (e.g., covariance, design matrix)
    # - Residuals and results
    # Conservative estimate: 100KB per row for complex operations
    bytes_per_row = 100 * 1024 
    
    if bytes_per_row == 0:
        return total_rows
        
    batch_size = min(total_rows, max(1, safe_mem // bytes_per_row))
    
    logger.log("batch_size_calculated",
               available_mem=safe_mem,
               bytes_per_row=bytes_per_row,
               calculated_batch_size=batch_size,
               total_rows=total_rows)
               
    return batch_size

def verify_batching_logic():
    """
    Verify that batch sizing logic works correctly.
    This is a utility function for testing, not part of the main pipeline.
    """
    total = 10000
    batch = calculate_batch_size(total)
    assert batch > 0 and batch <= total, "Batch size logic failed"
    logger.log("batching_verified", total=total, batch=batch)
    return True

if __name__ == "__main__":
    verify_batching_logic()
    print("Memory monitor verification passed.")
