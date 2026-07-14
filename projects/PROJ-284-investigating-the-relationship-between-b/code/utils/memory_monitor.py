from __future__ import annotations

import os
import sys
from typing import Optional, Tuple
import psutil
from code.logging_config import get_logger

logger = get_logger(__name__)

def get_available_memory() -> int:
    """
    Returns the available system memory in bytes.
    """
    try:
        mem = psutil.virtual_memory()
        return mem.available
    except Exception as e:
        logger.warning(f"Could not read memory info: {e}. Assuming default 4GB.")
        return 4 * 1024**3

def estimate_memory_usage(df_rows: int, df_cols: int, dtype_size: int = 8) -> int:
    """
    Estimates memory usage for a DataFrame in bytes.
    dtype_size defaults to 8 bytes (float64/int64).
    """
    # Approximate: rows * cols * bytes_per_value + overhead
    # Overhead is roughly 10-20% for pandas structures
    raw_size = df_rows * df_cols * dtype_size
    return int(raw_size * 1.2)

def calculate_batch_size(
    total_size_bytes: int, 
    memory_limit_gb: float, 
    chunk_multiplier: float = 0.5
) -> int:
    """
    Calculates a safe batch size (number of rows) to process given a total data size
    and a memory limit.
    
    Args:
        total_size_bytes: Total size of the dataset to be processed.
        memory_limit_gb: Maximum allowed memory usage in GB.
        chunk_multiplier: Fraction of memory limit to dedicate to the batch (0.5 = 50%).
    
    Returns:
        Estimated number of rows per batch.
    """
    limit_bytes = memory_limit_gb * 1024**3
    safe_memory = limit_bytes * chunk_multiplier
    
    if total_size_bytes == 0:
        return 1000 # Default small batch
    
    # Ratio of safe memory to total size gives us the fraction of data we can load at once
    fraction = safe_memory / total_size_bytes
    
    # We can't directly convert bytes to rows without knowing the schema,
    # so we assume a linear relationship and cap the batch size.
    # If we can load the whole thing, return a large number.
    if fraction >= 1.0:
        return 1000000
    
    # This is a heuristic. In a real scenario, we'd need to know rows/bytes ratio.
    # For CSV loading, pandas chunksize is in rows.
    # We'll estimate a "rows per byte" ratio based on a standard float row ~ 100 bytes (10 cols).
    estimated_rows_per_byte = 0.01 
    estimated_total_rows = total_size_bytes * estimated_rows_per_byte
    
    batch_rows = int(estimated_total_rows * fraction)
    
    # Ensure minimum batch size
    return max(100, batch_rows)

def verify_batching_logic():
    """
    Simple verification that the batching logic doesn't crash.
    """
    mem = get_available_memory()
    print(f"Available memory: {mem / 1024**3:.2f} GB")
    
    batch = calculate_batch_size(500 * 1024 * 1024, 7.0) # 500MB dataset
    print(f"Suggested batch size for 500MB dataset: {batch}")

if __name__ == "__main__":
    verify_batching_logic()
