"""
Memory monitoring utilities.
Implements T005 and T005b: Enforce ≤7GB limit via automatic sampling/subsetting.
"""
import os
import resource
import gc
import sys
from typing import Optional, Union
import pandas as pd
import numpy as np

class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds the limit and subsetting is impossible."""
    pass

def get_current_memory_mb() -> float:
    """Get current RSS memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # On Linux, ru_maxrss is in KB. On macOS, it is in bytes.
    # We normalize to MB.
    if sys.platform == 'darwin':
        return usage.ru_maxrss / (1024 * 1024)
    else:
        return usage.ru_maxrss / 1024.0

def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    if sys.platform == 'darwin':
        return usage.ru_maxrss / (1024 * 1024)
    else:
        return usage.ru_maxrss / 1024.0

def check_memory_limit(limit_mb: float = 7000) -> None:
    """
    Check if current memory usage exceeds limit.
    Raises MemoryLimitExceeded if limit is exceeded.
    """
    current = get_current_memory_mb()
    if current > limit_mb:
        raise MemoryLimitExceeded(f"Memory limit exceeded: {current:.2f} MB > {limit_mb} MB")

def enforce_memory_limit(limit_mb: float = 7000) -> None:
    """Enforce memory limit, raising exception if exceeded."""
    check_memory_limit(limit_mb)

def get_memory_usage_report() -> dict:
    """Get a report of memory usage."""
    return {
        'current_mb': get_current_memory_mb(),
        'limit_mb': 7000
    }

def simulate_large_memory_usage(size_mb: int) -> None:
    """Simulate large memory usage for testing."""
    data = bytearray(size_mb * 1024 * 1024)
    _ = len(data)

def cleanup_large_memory() -> None:
    """Attempt to cleanup large memory allocations."""
    gc.collect()

def estimate_dataframe_memory_mb(df: pd.DataFrame) -> float:
    """
    Estimate the memory usage of a pandas DataFrame in MB.
    """
    return df.memory_usage(deep=True).sum() / (1024 * 1024)

def check_and_subset_memory(
    df: pd.DataFrame,
    limit_gb: float = 7.0,
    min_sample_fraction: float = 0.01
) -> pd.DataFrame:
    """
    Check if the DataFrame fits within the memory limit.
    If it exceeds the limit, attempt to sample rows to reduce memory usage
    while maintaining statistical representativeness (stratified sampling if possible).
    
    If subsetting is impossible (e.g., single row > limit or sampling below min_fraction
    still exceeds limit), raise MemoryLimitExceeded.
    
    Args:
        df: The input DataFrame.
        limit_gb: The memory limit in GB (default 7.0).
        min_sample_fraction: The minimum fraction of rows to retain if subsetting.
        
    Returns:
        A DataFrame that fits within the memory limit (either original or subset).
        
    Raises:
        MemoryLimitExceeded: If the DataFrame cannot be reduced to fit the limit.
    """
    limit_mb = limit_gb * 1024
    current_memory_mb = estimate_dataframe_memory_mb(df)
    
    if current_memory_mb <= limit_mb:
        return df
    
    n_rows = len(df)
    n_cols = len(df.columns)
    
    # Estimate size per row in MB
    if n_rows == 0:
        return df
        
    bytes_per_row = current_memory_mb * 1024 * 1024 / n_rows
    
    # Calculate target number of rows to fit in limit
    target_rows = int(limit_mb * 1024 * 1024 / bytes_per_row)
    
    # Ensure we don't go below minimum sample fraction
    min_rows = max(1, int(n_rows * min_sample_fraction))
    
    if target_rows < min_rows:
        target_rows = min_rows
    
    # If target is still >= n_rows, we can't subset enough
    if target_rows >= n_rows:
        raise MemoryLimitExceeded(
            f"Memory limit exceeded ({current_memory_mb:.2f} MB > {limit_mb} MB) "
            f"and subsetting impossible (requires < {target_rows} rows, but min is {min_rows})"
        )
    
    # Attempt stratified sampling if a 'group' column exists, otherwise random
    if 'group' in df.columns:
        try:
            # Stratified sampling by group
            sampled_df = df.groupby('group', group_keys=False).apply(
                lambda x: x.sample(n=min(len(x), max(1, int(len(x) * (target_rows / n_rows))))),
                random_state=42
            )
        except Exception:
            # Fallback to random sampling if stratified fails
            sampled_df = df.sample(n=target_rows, random_state=42)
    else:
        sampled_df = df.sample(n=target_rows, random_state=42)
    
    # Verify the subset fits
    new_memory_mb = estimate_dataframe_memory_mb(sampled_df)
    if new_memory_mb > limit_mb:
        # If it still doesn't fit, try to reduce further iteratively
        while new_memory_mb > limit_mb and len(sampled_df) > min_rows:
            # Reduce by 10%
            new_n = max(min_rows, int(len(sampled_df) * 0.9))
            if new_n >= len(sampled_df):
                break
            sampled_df = sampled_df.sample(n=new_n, random_state=42)
            new_memory_mb = estimate_dataframe_memory_mb(sampled_df)
        
        if new_memory_mb > limit_mb:
            raise MemoryLimitExceeded(
                f"Memory limit exceeded ({new_memory_mb:.2f} MB > {limit_mb} MB) "
                f"and subsetting impossible (reached minimum sample size)"
            )
    
    return sampled_df.reset_index(drop=True)

def check_and_subset_memory_fallback(df: pd.DataFrame, limit_gb: float = 7.0) -> pd.DataFrame:
    """
    Wrapper for T005b: If check_and_subset_memory cannot reduce memory below limit,
    raise MemoryLimitExceeded with specific message.
    """
    try:
        return check_and_subset_memory(df, limit_gb)
    except MemoryLimitExceeded as e:
        if "subsetting impossible" in str(e):
            raise MemoryLimitExceeded("Memory limit exceeded and subsetting impossible")
        raise

# Aliases for compatibility
get_memory_mb = get_current_memory_mb
peak_memory_mb = get_peak_memory_mb
limit_mb = 7000
check_limit = check_memory_limit
enforce_limit = enforce_memory_limit
usage_report = get_memory_usage_report
simulate_memory = simulate_large_memory_usage
cleanup_memory = cleanup_large_memory
estimate_memory = estimate_dataframe_memory_mb
check_subset = check_and_subset_memory
check_subset_fallback = check_and_subset_memory_fallback
