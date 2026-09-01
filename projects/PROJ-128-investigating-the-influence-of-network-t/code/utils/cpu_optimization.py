"""
CPU Optimization Utilities for llmXive Pipeline

This module provides functions to ensure CPU-only execution, optimize memory usage,
and enforce deterministic behavior without GPU acceleration.
"""
import os
import sys
import gc
import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Any, Union
import warnings

# Explicitly disable GPU acceleration libraries if they are imported
# This prevents accidental GPU usage in libraries like PyTorch or TensorFlow
# even if they are not directly used in this project.
def validate_no_gpu_acceleration() -> bool:
    """
    Validates that no GPU acceleration is enabled in common ML libraries.
    Returns True if CPU-only mode is confirmed, False otherwise.
    """
    is_cpu_only = True

    # Check PyTorch if available
    try:
        import torch
        if torch.cuda.is_available():
            warnings.warn(
                "PyTorch GPU is available but should be disabled for CPU-only execution. "
                "Setting torch.cuda.is_available() check to False logically, but not modifying global state."
            )
            # In a real script, we would do: torch.cuda.is_available = lambda: False
            # But here we just warn and ensure we don't call .cuda()
            is_cpu_only = False
    except ImportError:
        pass

    # Check TensorFlow if available
    try:
        import tensorflow as tf
        if tf.config.list_physical_devices('GPU'):
            warnings.warn(
                "TensorFlow GPU is available. Ensure GPU is disabled for CPU-only execution."
            )
            is_cpu_only = False
    except ImportError:
        pass

    # Check JAX if available
    try:
        import jax
        if jax.local_devices(backend='gpu'):
            warnings.warn("JAX GPU devices detected.")
            is_cpu_only = False
    except ImportError:
        pass

    return is_cpu_only


def optimize_memory_usage(data: Union[np.ndarray, pd.DataFrame, List[Any]]) -> Any:
    """
    Optimizes memory usage of data structures by:
    1. Downcasting numeric types where possible.
    2. Converting to contiguous memory layout.
    3. Removing unnecessary object references.

    Args:
        data: Input data (numpy array, pandas DataFrame, or list).

    Returns:
        Memory-optimized version of the input data.
    """
    if isinstance(data, pd.DataFrame):
        # Downcast numeric columns
        for col in data.select_dtypes(include=['int64']).columns:
            data[col] = pd.to_numeric(data[col], downcast='integer')
        for col in data.select_dtypes(include=['float64']).columns:
            data[col] = pd.to_numeric(data[col], downcast='float')

        # Convert object columns to category if appropriate
        for col in data.select_dtypes(include=['object']).columns:
            if data[col].nunique() / len(data) < 0.5:  # If unique values < 50%
                data[col] = data[col].astype('category')

        # Ensure memory layout is contiguous
        if hasattr(data, '_values'):
            data = data.copy()

    elif isinstance(data, np.ndarray):
        if not data.flags['C_CONTIGUOUS']:
            data = np.ascontiguousarray(data)

        # Downcast if possible
        if np.issubdtype(data.dtype, np.floating):
            if data.dtype == np.float64:
                # Check if float32 would suffice (simple heuristic)
                if np.max(np.abs(data)) < 3.4e38 and np.min(np.abs(data)) > 1e-45:
                    # Only downcast if values are within float32 range
                    # This is a conservative check
                    pass  # Keep float64 for safety unless explicitly needed
            elif data.dtype == np.float32:
                pass

    elif isinstance(data, list):
        # For lists, we rely on the contained objects being optimized
        # or converted to arrays later
        pass

    return data


def chunked_dataframe_iterator(df: pd.DataFrame, chunk_size: int = 1000):
    """
    Iterates over a DataFrame in chunks to reduce memory pressure.
    Useful for processing large datasets that don't fit in memory.

    Args:
        df: Input DataFrame.
        chunk_size: Number of rows per chunk.

    Yields:
        DataFrame chunks.
    """
    num_rows = len(df)
    for start in range(0, num_rows, chunk_size):
        end = min(start + chunk_size, num_rows)
        yield df.iloc[start:end]


def set_random_seed(seed: int = 42) -> None:
    """
    Sets random seeds for reproducibility across numpy and python.
    Note: This does not set seeds for external libraries like sklearn or torch
    as they should be handled in their respective modules.

    Args:
        seed: Integer seed value.
    """
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)


def ensure_numpy_arrays_contiguous(arrays: List[np.ndarray]) -> List[np.ndarray]:
    """
    Ensures a list of numpy arrays are C-contiguous in memory.

    Args:
        arrays: List of numpy arrays.

    Returns:
        List of contiguous numpy arrays.
    """
    contiguous_arrays = []
    for arr in arrays:
        if not arr.flags['C_CONTIGUOUS']:
            arr = np.ascontiguousarray(arr)
        contiguous_arrays.append(arr)
    return contiguous_arrays


def force_gc_collect() -> int:
    """
    Forces a garbage collection cycle and returns the number of objects collected.
    Useful for debugging memory leaks in long-running processes.

    Returns:
        Number of objects collected.
    """
    collected = gc.collect()
    return collected
