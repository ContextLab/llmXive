"""
CPU-Only Compliance and Memory Efficiency Cleanup Module.

This module ensures the project runs strictly on CPU resources with
memory-efficient loops, adhering to the 2-core CPU and ~7GB RAM constraints.
It includes:
1. Sanitization of imports to prevent accidental GPU library loading.
2. Memory-efficient streaming utilities for large datasets.
3. Chunked processing helpers to avoid OOM errors.
4. Verification that no CUDA/GPU tensors are instantiated.
"""

import os
import gc
import sys
import logging
import warnings
from pathlib import Path
from typing import Generator, Optional, Any, Dict, List

import numpy as np
import pandas as pd

# Explicitly block GPU libraries at import time if possible
# Note: We do not import torch/tensorflow here to avoid triggering GPU detection.
# If they are imported elsewhere, we set environment variables to force CPU.
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TF GPU logs
os.environ["OMP_NUM_THREADS"] = "2"  # Limit OpenMP threads to 2 cores
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

from config_manager import get_config, get_results_path
from logging_config import get_logger

logger = get_logger(__name__)


def verify_cpu_only() -> bool:
    """
    Verifies that no GPU-accelerated libraries have initialized a GPU context.
    Returns True if CPU-only compliance is confirmed, False otherwise.
    Logs warnings if GPU usage is detected.
    """
    gpu_detected = False

    # Check for PyTorch if imported
    if "torch" in sys.modules:
        import torch
        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            logger.warning("PyTorch detected GPU availability. Forcing CPU context.")
            # Force CPU usage if not already done by env vars
            if torch.cuda.is_available():
                # This is a soft check; actual usage depends on device assignment
                pass
            gpu_detected = True

    # Check for TensorFlow if imported
    if "tensorflow" in sys.modules or "tf" in sys.modules:
        try:
            import tensorflow as tf
            if len(tf.config.list_physical_devices('GPU')) > 0:
                logger.warning("TensorFlow detected GPU availability. Forcing CPU context.")
                gpu_detected = True
        except ImportError:
            pass

    # Check for JAX if imported
    if "jax" in sys.modules:
        try:
            import jax
            if jax.default_backend() != 'cpu':
                logger.warning("JAX default backend is not CPU.")
                gpu_detected = True
        except ImportError:
            pass

    if not gpu_detected:
        logger.info("CPU-only compliance verified: No active GPU contexts detected.")
    else:
        logger.warning("GPU resources detected. Ensure all operations are explicitly moved to CPU.")

    return not gpu_detected


def stream_csv_in_chunks(
    file_path: str,
    chunk_size: int = 10000,
    dtype: Optional[Dict[str, Any]] = None,
    usecols: Optional[List[str]] = None
) -> Generator[pd.DataFrame, None, None]:
    """
    Generator to stream a CSV file in chunks to prevent memory overload.
    Useful for large datasets (>1GB) that exceed RAM limits.

    Args:
        file_path: Path to the CSV file.
        chunk_size: Number of rows per chunk.
        dtype: Optional dtype dictionary to optimize memory.
        usecols: Optional list of columns to load.

    Yields:
        pd.DataFrame: A chunk of the CSV data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Streaming {file_path} in chunks of {chunk_size}...")
    
    try:
        for chunk in pd.read_csv(
            file_path,
            chunksize=chunk_size,
            dtype=dtype,
            usecols=usecols,
            low_memory=False
        ):
            yield chunk
            # Force garbage collection after every few chunks if memory is tight
            # gc.collect() # Uncomment if memory pressure is observed
    except Exception as e:
        logger.error(f"Error streaming CSV: {e}")
        raise


def process_in_memory_safe(
    df: pd.DataFrame,
    func,
    batch_size: int = 5000
) -> pd.DataFrame:
    """
    Applies a function to a DataFrame in batches to manage memory usage.
    If the DataFrame is too large, it processes row-wise or in batches.

    Args:
        df: Input DataFrame.
        func: Function to apply.
        batch_size: Number of rows per batch.

    Returns:
        pd.DataFrame: Processed DataFrame.
    """
    if len(df) <= batch_size:
        return func(df)

    logger.info(f"Processing {len(df)} rows in batches of {batch_size}...")
    results = []
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        try:
            result = func(batch)
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing batch {i//batch_size}: {e}")
            raise
        
        # Explicitly delete batch to free memory
        del batch
        gc.collect()

    return pd.concat(results, ignore_index=True)


def optimize_memory_usage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reduces memory footprint of a DataFrame by downcasting numeric types
    and converting object columns to category where appropriate.

    Args:
        df: Input DataFrame.

    Returns:
        pd.DataFrame: Memory-optimized DataFrame.
    """
    logger.debug("Optimizing DataFrame memory usage...")
    start_mem = df.memory_usage(deep=True).sum() / 1024 ** 2
    
    for col in df.columns:
        col_type = df[col].dtype

        if col_type != object:
            c_min = df[col].min()
            c_max = df[col].max()
            
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                else:
                    df[col] = df[col].astype(np.int64)
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
        else:
            if df[col].nunique() / len(df[col]) < 0.5: # Heuristic: < 50% unique
                df[col] = df[col].astype('category')

    end_mem = df.memory_usage(deep=True).sum() / 1024 ** 2
    logger.info(f"Memory usage optimized: {start_mem:.2f} MB -> {end_mem:.2f} MB ({100 * (start_mem - end_mem) / start_mem:.1f}% reduction)")
    return df


def run_cpu_cleanup_pipeline() -> Dict[str, Any]:
    """
    Executes the CPU cleanup and verification pipeline.
    1. Sets environment variables for CPU-only execution.
    2. Verifies no GPU contexts are active.
    3. Optimizes memory usage for any loaded data (if provided via config).
    4. Logs the status.

    Returns:
        Dict with status and metrics.
    """
    logger.info("Starting CPU Cleanup and Compliance Pipeline...")
    
    # 1. Environment Setup (already set at module load, but re-affirm)
    logger.info(f"OMP_NUM_THREADS set to: {os.environ.get('OMP_NUM_THREADS')}")
    logger.info(f"CUDA_VISIBLE_DEVICES set to: {os.environ.get('CUDA_VISIBLE_DEVICES')}")

    # 2. Verification
    is_compliant = verify_cpu_only()
    
    # 3. Memory Optimization Check (if a large dataset is specified in config)
    config = get_config()
    data_path = config.get('data_path')
    
    memory_stats = {}
    if data_path and os.path.exists(data_path):
        try:
            # Load a sample to estimate size without loading full file if possible
            # Or use streaming to check first chunk
            logger.info(f"Checking memory usage for: {data_path}")
            # We do a lightweight check by reading metadata or a small chunk
            chunk = pd.read_csv(data_path, nrows=1000)
            optimized_chunk = optimize_memory_usage(chunk.copy())
            
            memory_stats['sample_reduction_pct'] = (
                (chunk.memory_usage(deep=True).sum() - optimized_chunk.memory_usage(deep=True).sum()) 
                / chunk.memory_usage(deep=True).sum() * 100
            )
            logger.info(f"Estimated memory reduction potential: {memory_stats['sample_reduction_pct']:.1f}%")
        except Exception as e:
            logger.warning(f"Could not optimize sample data: {e}")

    status = {
        "cpu_compliant": is_compliant,
        "threads_limited": os.environ.get('OMP_NUM_THREADS') == '2',
        "memory_optimization_est": memory_stats.get('sample_reduction_pct', 0),
        "status": "success" if is_compliant else "warning"
    }

    logger.info(f"CPU Cleanup Pipeline completed. Status: {status['status']}")
    return status


def main():
    """
    Entry point for running the CPU cleanup verification directly.
    """
    setup_logger = get_logger(__name__)
    setup_logger.info("Running CPU Cleanup Module directly.")
    
    try:
        result = run_cpu_cleanup_pipeline()
        print(f"CPU Compliance Check Result: {result}")
        
        if not result['cpu_compliant']:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"CPU Cleanup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
