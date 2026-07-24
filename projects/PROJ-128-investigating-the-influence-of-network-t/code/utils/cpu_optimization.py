"""
CPU Optimization Utilities for llmXive Pipeline.

This module ensures all heavy numerical operations are strictly CPU-bound
and optimized for the project's resource constraints (no GPU, limited RAM).
It enforces environment variables and configures libraries to prevent
accidental GPU offloading or excessive memory usage.
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Any

# Enforce CPU-only environment variables at module import time
# This prevents TensorFlow/PyTorch (if accidentally imported later) from
# attempting to initialize CUDA or claiming GPU resources.
def _enforce_cpu_only() -> None:
    """Set environment variables to force CPU-only execution."""
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    
    # For libraries that might respect these
    os.environ["OMP_NUM_THREADS"] = "4"  # Limit OpenMP threads
    os.environ["MKL_NUM_THREADS"] = "4"  # Limit MKL threads
    os.environ["OPENBLAS_NUM_THREADS"] = "4"
    
    # Explicitly disable GPU for common frameworks if they are loaded later
    # (Note: We don't import them here to avoid hard dependencies, 
    # but setting these env vars helps if they are imported downstream)

# Execute enforcement immediately
_enforce_cpu_only()

def optimize_memory_usage(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
    """
    Downcast numeric columns to reduce memory footprint.
    
    This is critical for large HCP datasets to stay within RAM limits.
    Integers are downcast to the smallest type that fits the range.
    Floats are downcast from float64 to float32 where precision allows.
    
    Args:
        df: Input DataFrame.
        inplace: If True, modify the DataFrame in place.
        
    Returns:
        The optimized DataFrame.
    """
    if not inplace:
        df = df.copy()

    int_cols = df.select_dtypes(include=['int64']).columns
    float_cols = df.select_dtypes(include=['float64']).columns

    for col in int_cols:
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

    for col in float_cols:
        c_min = df[col].min()
        c_max = df[col].max()
        # Check if float32 is sufficient (approx 7 decimal digits)
        # For most neuroimaging metrics, float32 is sufficient and halves memory.
        if c_min >= np.finfo(np.float32).min and c_max <= np.finfo(np.float32).max:
            df[col] = df[col].astype(np.float32)
        else:
            df[col] = df[col].astype(np.float64)

    return df

def validate_no_gpu_acceleration() -> bool:
    """
    Validates that no GPU devices are visible to the process.
    
    Returns:
        True if CPU-only mode is confirmed, False otherwise.
    """
    # Check environment variable
    if os.getenv("CUDA_VISIBLE_DEVICES", "") != "":
        return False
    
    # Try to check torch if available, but don't fail if not installed
    try:
        import torch
        if torch.cuda.is_available():
            return False
    except ImportError:
        pass
    
    # Try to check tensorflow if available
    try:
        import tensorflow as tf
        if tf.config.list_physical_devices('GPU'):
            return False
    except ImportError:
        pass
    
    return True

def chunked_dataframe_iterator(df: pd.DataFrame, chunk_size: int = 1000):
    """
    Generator to iterate over a DataFrame in chunks to save memory.
    
    Args:
        df: Input DataFrame.
        chunk_size: Number of rows per chunk.
        
    Yields:
        DataFrame chunks.
    """
    for i in range(0, len(df), chunk_size):
        yield df.iloc[i:i + chunk_size]

def set_random_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across numpy and pandas.
    
    Args:
        seed: Integer seed value.
    """
    np.random.seed(seed)
    # Pandas relies on numpy for random state in most operations

def ensure_numpy_arrays_contiguous(arrays: List[np.ndarray]) -> List[np.ndarray]:
    """
    Ensure numpy arrays are contiguous in memory for optimal CPU cache usage.
    
    Args:
        arrays: List of numpy arrays.
        
    Returns:
        List of contiguous arrays.
    """
    return [np.ascontiguousarray(arr) for arr in arrays]

# Run a sanity check on import
if __name__ == "__main__":
    if not validate_no_gpu_acceleration():
        print("WARNING: GPU devices detected. CPU-only mode may not be enforced.")
        sys.exit(1)
    else:
        print("CPU-only mode verified successfully.")
    
    # Test memory optimization
    test_df = pd.DataFrame({
        'a': np.random.randint(0, 100, 1000),
        'b': np.random.rand(1000).astype(np.float64)
    })
    original_memory = test_df.memory_usage(deep=True)
    optimized_df = optimize_memory_usage(test_df)
    optimized_memory = optimized_df.memory_usage(deep=True)
    
    print(f"Original memory: {original_memory} bytes")
    print(f"Optimized memory: {optimized_memory} bytes")
    print(f"Reduction: {100 * (1 - optimized_memory / original_memory):.2f}%")
