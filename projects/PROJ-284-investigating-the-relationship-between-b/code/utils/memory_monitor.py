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
    
    Returns:
        int: Available memory in bytes
    """
    try:
        mem = psutil.virtual_memory()
        available = mem.available
        logger.log("get_available_memory", available_bytes=available)
        return available
    except Exception as e:
        logger.log("get_available_memory", error=str(e), fallback=True)
        # Fallback: assume 4GB if psutil fails
        return 4 * 1024 * 1024 * 1024

def estimate_memory_usage(matrix_size: Tuple[int, int], dtype_size: int = 8) -> int:
    """
    Estimate memory usage for a matrix of given size.
    
    Args:
        matrix_size: Tuple of (rows, cols)
        dtype_size: Size of data type in bytes (default 8 for float64)
    
    Returns:
        int: Estimated memory usage in bytes
    """
    rows, cols = matrix_size
    return rows * cols * dtype_size

def calculate_batch_size(
    item_size_bytes: int,
    max_memory_gb: float = 7.0,
    safety_factor: float = 0.8
) -> int:
    """
    Calculate optimal batch size given item size and memory constraints.
    
    Args:
        item_size_bytes: Size of one item (e.g., one subject's matrix) in bytes
        max_memory_gb: Maximum memory to use in GB
        safety_factor: Safety factor to leave headroom (0.0 to 1.0)
    
    Returns:
        int: Recommended batch size
    """
    available_bytes = get_available_memory()
    safe_limit_bytes = int(available_bytes * safety_factor)
    
    # Also respect the explicit max_memory_gb limit
    max_limit_bytes = int(max_memory_gb * 1024 * 1024 * 1024)
    effective_limit = min(safe_limit_bytes, max_limit_bytes)
    
    if item_size_bytes <= 0:
        return 100 # Default fallback
    
    batch_size = effective_limit // item_size_bytes
    
    logger.log("calculate_batch_size", 
             item_size=item_size_bytes,
             available_bytes=available_bytes,
             limit_bytes=effective_limit,
             batch_size=batch_size)
    
    return max(1, batch_size)
