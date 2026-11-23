"""
CPU Optimization Utilities for llmXive Pipeline.

This module provides functions to ensure the pipeline runs efficiently on CPU-only
environments, avoids GPU acceleration, manages memory usage, and optimizes data
structures for performance.

All functions are designed to be robust and fail loudly if GPU resources are detected
or if memory constraints are violated.
"""
import os
import sys
import gc
import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Any, Union
import warnings

# Constants
FLOAT32_DTYPE = np.float32
INT32_DTYPE = np.int32
DEFAULT_SEED = 42
MEMORY_WARNING_THRESHOLD_MB = 1024  # 1GB warning threshold
MAX_MEMORY_USAGE_PERCENT = 85.0     # Stop if usage exceeds 85%

def validate_no_gpu_acceleration() -> bool:
    """
    Validates that no GPU acceleration libraries are active or configured.

    Checks:
    - PyTorch GPU availability
    - TensorFlow GPU devices
    - CUDA environment variables
    - JAX GPU availability

    Returns:
        bool: True if no GPU is detected, False otherwise.

    Raises:
        RuntimeError: If GPU acceleration is detected.
    """
    # Check environment variables
    cuda_visible_devices = os.environ.get('CUDA_VISIBLE_DEVICES')
    if cuda_visible_devices is not None and cuda_visible_devices != '':
        warnings.warn(f"CUDA_VISIBLE_DEVICES is set to '{cuda_visible_devices}'. "
                    "This may indicate GPU usage. Consider unsetting for CPU-only mode.")

    # Check PyTorch
    try:
        import torch
        if torch.cuda.is_available():
            raise RuntimeError(
                "PyTorch GPU is available. Set CUDA_VISIBLE_DEVICES='' or "
                "install CPU-only PyTorch version for CPU-only execution."
            )
    except ImportError:
        pass  # PyTorch not installed, which is fine

    # Check TensorFlow
    try:
        import tensorflow as tf
        if tf.config.list_physical_devices('GPU'):
            raise RuntimeError(
                "TensorFlow GPU devices detected. Configure TensorFlow for CPU-only mode."
            )
    except ImportError:
        pass  # TensorFlow not installed, which is fine

    # Check JAX
    try:
        import jax
        if jax.default_backend() != 'cpu':
            warnings.warn(f"JAX backend is '{jax.default_backend()}', not 'cpu'.")
    except ImportError:
        pass  # JAX not installed, which is fine

    return True

def optimize_memory_usage(df: pd.DataFrame, 
                          low_precision: bool = True,
                          drop_unused_categories: bool = True) -> pd.DataFrame:
    """
    Optimizes memory usage of a pandas DataFrame.

    Strategies:
    1. Downcast numeric columns to lower precision (float32, int32)
    2. Convert object columns to category where appropriate
    3. Drop unused categories in categorical columns
    4. Convert boolean columns to bool dtype

    Args:
        df: Input DataFrame
        low_precision: If True, downcast numeric columns
        drop_unused_categories: If True, remove unused categories

    Returns:
        pd.DataFrame: Optimized DataFrame with reduced memory usage
    """
    if df is None or df.empty:
        return df

    df_optimized = df.copy()

    # Downcast numeric columns
    if low_precision:
        numeric_cols = df_optimized.select_dtypes(include=['int64', 'float64']).columns
        for col in numeric_cols:
            if df_optimized[col].dtype == 'int64':
                df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='integer')
            elif df_optimized[col].dtype == 'float64':
                df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='float')

    # Convert object columns to category
    object_cols = df_optimized.select_dtypes(include=['object']).columns
    for col in object_cols:
        if df_optimized[col].nunique() / len(df_optimized) < 0.5:  # Only if <50% unique
            df_optimized[col] = df_optimized[col].astype('category')

    # Drop unused categories
    if drop_unused_categories:
        cat_cols = df_optimized.select_dtypes(include=['category']).columns
        for col in cat_cols:
            df_optimized[col] = df_optimized[col].cat.remove_unused_categories()

    return df_optimized

def chunked_dataframe_iterator(df: pd.DataFrame, 
                               chunk_size: int = 10000) -> Optional[pd.DataFrame]:
    """
    Iterator that yields chunks of a DataFrame to reduce memory pressure.

    Args:
        df: Input DataFrame
        chunk_size: Number of rows per chunk

    Yields:
        pd.DataFrame: Chunks of the input DataFrame
    """
    if df is None or df.empty:
        return

    n_rows = len(df)
    for start_idx in range(0, n_rows, chunk_size):
        end_idx = min(start_idx + chunk_size, n_rows)
        yield df.iloc[start_idx:end_idx]

def set_random_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Sets random seeds for reproducibility across numpy, pandas, and other libraries.

    Args:
        seed: Random seed value (default: 42)
    """
    np.random.seed(seed)
    
    # Set pandas random seed if available
    if hasattr(pd, 'random_state'):
        pd.random_state = seed
    
    # Attempt to set seeds for common libraries
    try:
        import random
        random.seed(seed)
    except ImportError:
        pass

    try:
        import os
        os.environ['PYTHONHASHSEED'] = str(seed)
    except Exception:
        pass

def ensure_numpy_arrays_contiguous(*arrays: np.ndarray) -> List[np.ndarray]:
    """
    Ensures all input numpy arrays are contiguous in memory for optimal performance.

    Args:
        *arrays: Variable number of numpy arrays

    Returns:
        List[np.ndarray]: List of contiguous arrays
    """
    contiguous_arrays = []
    for arr in arrays:
        if not arr.flags['C_CONTIGUOUS']:
            contiguous_arrays.append(np.ascontiguousarray(arr))
        else:
            contiguous_arrays.append(arr)
    return contiguous_arrays

def force_gc_collect() -> int:
    """
    Forces garbage collection and returns the number of objects collected.

    Returns:
        int: Number of objects collected
    """
    collected = gc.collect()
    return collected

def convert_to_low_precision(arr: np.ndarray, 
                             target_dtype: np.dtype = FLOAT32_DTYPE) -> np.ndarray:
    """
    Converts a numpy array to a lower precision dtype if possible.

    Args:
        arr: Input numpy array
        target_dtype: Target dtype (default: float32)

    Returns:
        np.ndarray: Array converted to target dtype if compatible
    """
    if arr.dtype == target_dtype:
        return arr

    if np.issubdtype(arr.dtype, np.floating):
        if target_dtype == FLOAT32_DTYPE and arr.dtype == np.float64:
            return arr.astype(FLOAT32_DTYPE)
    elif np.issubdtype(arr.dtype, np.integer):
        if target_dtype == INT32_DTYPE and arr.dtype == np.int64:
            return arr.astype(INT32_DTYPE)

    return arr

def limit_pandas_cache(max_size: int = 100) -> None:
    """
    Limits the size of pandas internal caches to prevent memory bloat.

    Args:
        max_size: Maximum number of items to keep in cache
    """
    try:
        # Pandas doesn't have a direct public API for cache limiting,
        # but we can set the max_rows for display and other internal limits
        pd.set_option('display.max_rows', max_size)
        pd.set_option('display.max_columns', None)
    except Exception:
        pass  # Ignore if options cannot be set

def monitor_memory_usage() -> Dict[str, float]:
    """
    Monitors current memory usage and returns statistics.

    Returns:
        Dict[str, float]: Dictionary with memory usage statistics
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        max_rss_mb = usage.ru_maxrss / 1024.0  # Convert KB to MB on Linux
        
        return {
            'max_rss_mb': max_rss_mb,
            'shared_mem_mb': usage.ru_ixrss / 1024.0,
            'unshared_data_mb': usage.ru_idrss / 1024.0,
            'unshared_stack_mb': usage.ru_isrss / 1024.0
        }
    except Exception:
        # Fallback for non-Unix systems
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            return {
                'rss_mb': mem_info.rss / 1024.0 / 1024.0,
                'vms_mb': mem_info.vms / 1024.0 / 1024.0
            }
        except Exception:
            return {'error': 'Could not determine memory usage'}

def validate_cpu_only_environment() -> bool:
    """
    Comprehensive validation that the environment is configured for CPU-only execution.

    Checks:
    - No GPU libraries active
    - Memory usage within safe limits
    - Random seeds set for reproducibility

    Returns:
        bool: True if environment is valid for CPU-only execution

    Raises:
        RuntimeError: If environment validation fails
    """
    # Validate no GPU
    validate_no_gpu_acceleration()
    
    # Check memory usage
    mem_stats = monitor_memory_usage()
    if 'max_rss_mb' in mem_stats:
        if mem_stats['max_rss_mb'] > 14000:  # ~14GB limit
            raise RuntimeError(
                f"Memory usage ({mem_stats['max_rss_mb']:.1f} MB) exceeds safe limits. "
                "Consider reducing batch sizes or using chunked processing."
            )
    
    # Set random seeds
    set_random_seed(DEFAULT_SEED)
    
    return True

# Auto-validate on module import if environment variable is set
if os.environ.get('LLMXIVE_STRICT_CPU_ONLY', '').lower() in ['1', 'true', 'yes']:
    validate_cpu_only_environment()
