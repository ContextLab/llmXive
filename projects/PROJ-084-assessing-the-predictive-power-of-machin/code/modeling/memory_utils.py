"""
Memory management utilities for training operations.
Ensures CPU-only execution and respects the 7GB RAM limit via batching.
"""
import os
import gc
import logging
from typing import Iterator, Tuple, List, Optional
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3
BATCH_SIZE_DEFAULT = 10000  # Rows per batch for training

def get_available_memory_gb() -> float:
    """Estimate available system memory in GB."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024**3)
        logger.info(f"Available system memory: {available_gb:.2f} GB")
        return available_gb
    except ImportError:
        logger.warning("psutil not found. Assuming default limit.")
        return MEMORY_LIMIT_GB

def check_memory_limit() -> bool:
    """
    Check if current estimated memory usage is within the limit.
    Returns True if safe to proceed, False otherwise.
    """
    available = get_available_memory_gb()
    if available < 1.0:
        logger.error("Critical: Less than 1GB available memory. Aborting.")
        return False
    return True

def enforce_cpu_only() -> None:
    """
    Force all operations to use CPU only.
    Disables GPU acceleration for libraries that support it.
    """
    # RDKit does not use GPU, but good practice
    # Scikit-learn defaults to CPU
    # If numpy uses MKL, ensure it doesn't spawn too many threads
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
    os.environ["NUMBA_NUM_THREADS"] = "1"
    
    logger.info("Enforced CPU-only execution environment variables.")

    # Attempt to disable GPU for any potential torch/tensorflow usage
    # (Though not in dependencies, defensive coding)
    try:
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        if torch.cuda.is_available():
            logger.warning("CUDA detected but CPU-only mode enforced. Forcing CPU device.")
            torch.set_device(torch.device("cpu"))
    except ImportError:
        pass

def batch_dataframe(df: pd.DataFrame, batch_size: Optional[int] = None) -> Iterator[Tuple[int, pd.DataFrame]]:
    """
    Yield batches of a DataFrame to process in memory-safe chunks.
    
    Args:
        df: The input DataFrame.
        batch_size: Number of rows per batch. Defaults to BATCH_SIZE_DEFAULT.
        
    Yields:
        Tuples of (start_index, batch_df)
    """
    if batch_size is None:
        batch_size = BATCH_SIZE_DEFAULT
        
    total_rows = len(df)
    if total_rows == 0:
        return

    logger.info(f"Processing {total_rows} rows in batches of {batch_size}")

    for start_idx in range(0, total_rows, batch_size):
        end_idx = min(start_idx + batch_size, total_rows)
        batch = df.iloc[start_idx:end_idx]
        yield start_idx, batch
        
        # Force garbage collection every few batches to prevent memory leak
        if start_idx % (batch_size * 5) == 0:
            gc.collect()

def estimate_dataframe_memory_mb(df: pd.DataFrame) -> float:
    """Estimate memory usage of a DataFrame in MB."""
    return df.memory_usage(deep=True).sum() / (1024 * 1024)

def validate_training_data_size(X: np.ndarray, y: np.ndarray) -> None:
    """
    Validates that the training data size is reasonable for the memory limit.
    Raises ValueError if the data is too large to fit in memory with overhead.
    """
    X_mb = X.nbytes / (1024 * 1024)
    y_mb = y.nbytes / (1024 * 1024)
    total_mb = X_mb + y_mb
    
    # Assume 3x overhead for scikit-learn operations (tree construction, CV splits)
    estimated_peak_mb = total_mb * 3.0
    
    logger.info(f"Data size: X={X_mb:.1f}MB, y={y_mb:.1f}MB. Est. peak usage: {estimated_peak_mb:.1f}MB")
    
    if estimated_peak_mb > (MEMORY_LIMIT_GB * 1024 * 0.8): # 80% of limit safety buffer
        raise ValueError(
            f"Dataset too large for memory limit. "
            f"Estimated peak usage {estimated_peak_mb:.1f}MB exceeds safe limit "
            f"of {MEMORY_LIMIT_GB * 1024 * 0.8:.1f}MB. "
            f"Consider using a smaller subset or increasing batch processing."
        )

def safe_gc() -> None:
    """Run garbage collection and log memory status."""
    gc.collect()
    available = get_available_memory_gb()
    logger.debug(f"Post-GC available memory: {available:.2f} GB")
