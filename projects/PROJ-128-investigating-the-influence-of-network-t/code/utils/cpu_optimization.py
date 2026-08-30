import os
import sys
import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Any
import gc

def optimize_memory_usage(df: pd.DataFrame, threshold_mb: float = 100.0) -> pd.DataFrame:
    """
    Optimize memory usage of a pandas DataFrame by downcasting numeric columns
    and removing unnecessary object overhead.

    Args:
        df: Input DataFrame
        threshold_mb: Memory threshold in MB. If DataFrame size > threshold, optimize.

    Returns:
        Optimized DataFrame
    """
    if df.memory_usage(deep=True).sum() / (1024 ** 2) <= threshold_mb:
        return df

    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type == np.float64:
            df[col] = df[col].astype(np.float32)
        elif col_type == np.int64:
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min >= np.iinfo(np.int8).min and c_max <= np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif c_min >= np.iinfo(np.int16).min and c_max <= np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif c_min >= np.iinfo(np.int32).min and c_max <= np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
        elif col_type == 'object':
            if df[col].nunique() / len(df[col]) < 0.5:
                df[col] = df[col].astype('category')
    
    gc.collect()
    return df

def validate_no_gpu_acceleration() -> bool:
    """
    Verify that no GPU acceleration libraries are being used.
    Checks for common GPU-related imports and environment variables.

    Returns:
        True if no GPU acceleration detected, False otherwise.
    """
    gpu_detected = False
    
    # Check environment variables
    if 'CUDA_VISIBLE_DEVICES' in os.environ:
        if os.environ['CUDA_VISIBLE_DEVICES'] != '-1':
            gpu_detected = True
    
    # Check for torch usage (if imported elsewhere in the pipeline)
    if 'torch' in sys.modules:
        import torch
        if torch.cuda.is_available():
            gpu_detected = True
    
    # Check for tensorflow usage
    if 'tensorflow' in sys.modules:
        import tensorflow as tf
        if tf.config.list_physical_devices('GPU'):
            gpu_detected = True
    
    # Check for cupy usage
    if 'cupy' in sys.modules:
        gpu_detected = True
    
    if gpu_detected:
        raise RuntimeError(
            "GPU acceleration detected. This project must run on CPU only. "
            "Set CUDA_VISIBLE_DEVICES=-1 or remove GPU-dependent code."
        )
    
    return True

def chunked_dataframe_iterator(
    df: pd.DataFrame, 
    chunk_size: int = 1000
) -> pd.DataFrame:
    """
    Iterator that yields chunks of a DataFrame to reduce memory pressure.

    Args:
        df: Input DataFrame
        chunk_size: Number of rows per chunk

    Yields:
        DataFrame chunks
    """
    n_rows = len(df)
    for start_idx in range(0, n_rows, chunk_size):
        end_idx = min(start_idx + chunk_size, n_rows)
        yield df.iloc[start_idx:end_idx].copy()

def set_random_seed(seed: int = 42) -> None:
    """
    Set random seed for reproducibility across numpy and pandas.

    Args:
        seed: Random seed value
    """
    np.random.seed(seed)
    # Note: pandas doesn't have a global seed, but numpy operations
    # used internally will respect this

def ensure_numpy_arrays_contiguous(arrays: List[np.ndarray]) -> List[np.ndarray]:
    """
    Ensure all numpy arrays are contiguous in memory for CPU efficiency.

    Args:
        arrays: List of numpy arrays

    Returns:
        List of contiguous numpy arrays
    """
    contiguous_arrays = []
    for arr in arrays:
        if not arr.flags['C_CONTIGUOUS']:
            arr = np.ascontiguousarray(arr)
        contiguous_arrays.append(arr)
    return contiguous_arrays
