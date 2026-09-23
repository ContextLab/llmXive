"""
Memory monitoring utilities for the fMRI analysis pipeline.

Implements FR-006: Track RAM usage and trigger downsampling if >6GB.
Ensures the pipeline stays within the compute budget (~7GB RAM limit).
"""
import gc
import logging
import os
import sys
from typing import Callable, Optional, Dict, Any, List, Union
from pathlib import Path

import psutil
import numpy as np

# Configuration constants
MEMORY_THRESHOLD_GB = 6.0
SAFETY_MARGIN_GB = 0.5  # Trigger at 6GB to stay under 7GB total budget
LOG_LEVEL = logging.INFO

# Setup logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(LOG_LEVEL)

def get_current_memory_usage_gb() -> float:
    """
    Get the current memory usage of the Python process in GB.
    
    Returns:
        float: Current memory usage in gigabytes.
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    # RSS (Resident Set Size) is the non-swapped physical memory
    memory_gb = memory_info.rss / (1024 ** 3)
    logger.debug(f"Current memory usage: {memory_gb:.2f} GB")
    return memory_gb

def check_memory_threshold(current_usage_gb: Optional[float] = None) -> bool:
    """
    Check if current memory usage exceeds the threshold.
    
    Args:
        current_usage_gb: Optional pre-calculated usage. If None, calculates fresh.
        
    Returns:
        bool: True if usage exceeds threshold, False otherwise.
    """
    if current_usage_gb is None:
        current_usage_gb = get_current_memory_usage_gb()
    
    threshold = MEMORY_THRESHOLD_GB
    is_over = current_usage_gb > threshold
    
    if is_over:
        logger.warning(
            f"Memory threshold exceeded: {current_usage_gb:.2f} GB > {threshold:.2f} GB"
        )
    else:
        logger.debug(
            f"Memory usage OK: {current_usage_gb:.2f} GB <= {threshold:.2f} GB"
        )
        
    return is_over

def trigger_gc() -> None:
    """
    Force garbage collection to free up unused memory.
    """
    logger.info("Triggering garbage collection...")
    gc.collect()
    logger.info("Garbage collection complete.")

def downsample_data(
    data: Union[np.ndarray, List[np.ndarray]],
    target_fraction: float = 0.5
) -> Union[np.ndarray, List[np.ndarray]]:
    """
    Downsample data arrays to reduce memory footprint.
    
    This function performs temporal downsampling by selecting every Nth timepoint
    or randomly sampling a fraction of the data.
    
    Args:
        data: Input data array (timepoints x features) or list of such arrays.
        target_fraction: Fraction of data to keep (0.0 to 1.0). Default 0.5.
        
    Returns:
        Downsampled data in the same format as input.
        
    Raises:
        ValueError: If target_fraction is not between 0 and 1.
        TypeError: If data format is unsupported.
    """
    if not 0.0 < target_fraction <= 1.0:
        raise ValueError(f"target_fraction must be between 0 and 1, got {target_fraction}")
    
    if isinstance(data, list):
        return [downsample_data(arr, target_fraction) for arr in data]
        
    if not isinstance(data, np.ndarray):
        raise TypeError(f"Unsupported data type: {type(data)}. Expected np.ndarray or list.")
        
    if data.ndim == 0:
        return data
        
    if data.ndim == 1:
        # 1D array: select indices
        n_samples = len(data)
        n_keep = max(1, int(n_samples * target_fraction))
        indices = np.linspace(0, n_samples - 1, n_keep, dtype=int)
        return data[indices]
        
    if data.ndim >= 2:
        # Multi-dimensional: downsample along the first axis (time)
        n_timepoints = data.shape[0]
        n_keep = max(1, int(n_timepoints * target_fraction))
        indices = np.linspace(0, n_timepoints - 1, n_keep, dtype=int)
        return data[indices, ...]
        
    return data

def monitor_and_ensure_memory(
    check_interval_gb: float = 0.5,
    max_iterations: int = 3,
    downsample_factor: float = 0.75
) -> bool:
    """
    Monitor memory and attempt to free up space if threshold is exceeded.
    
    This function checks memory usage, and if over threshold, attempts to:
    1. Trigger garbage collection
    2. Downsample cached data if available (requires external cache hook)
    
    Args:
        check_interval_gb: How much memory to check before re-evaluating.
        max_iterations: Maximum number of downsample attempts before failing.
        downsample_factor: Factor to reduce data size on each attempt.
        
    Returns:
        bool: True if memory is within limits after attempts, False otherwise.
        
    Note:
        This function logs warnings but does not raise exceptions. 
        It is the caller's responsibility to handle the return value.
    """
    current = get_current_memory_usage_gb()
    logger.info(f"Starting memory check. Current usage: {current:.2f} GB")
    
    if not check_memory_threshold(current):
        return True
        
    for attempt in range(1, max_iterations + 1):
        logger.warning(
            f"Memory over threshold. Attempting recovery (attempt {attempt}/{max_iterations})..."
        )
        
        # Step 1: Garbage collection
        trigger_gc()
        current = get_current_memory_usage_gb()
        logger.info(f"After GC: {current:.2f} GB")
        
        if not check_memory_threshold(current):
            logger.info("Memory recovered successfully via GC.")
            return True
            
        # Note: Actual data downsampling requires access to the data cache,
        # which is handled by the calling context (e.g., ROI extractor or GLM fitter).
        # This function signals the need for downsampling but cannot access 
        # the data structures directly without coupling.
        logger.warning(
            "GC insufficient. Caller must downsample data or reduce batch size."
        )
        
    logger.error(
        f"Failed to recover memory after {max_iterations} attempts. "
        f"Current usage: {get_current_memory_usage_gb():.2f} GB."
    )
    return False

def main() -> None:
    """
    Command-line entry point for memory monitoring.
    
    Usage:
        python -m code.utils.memory_monitor [--check]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory monitoring utility")
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Check current memory usage and exit"
    )
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=MEMORY_THRESHOLD_GB,
        help=f"Memory threshold in GB (default: {MEMORY_THRESHOLD_GB})"
    )
    
    args = parser.parse_args()
    
    if args.check:
        usage = get_current_memory_usage_gb()
        print(f"Current memory usage: {usage:.2f} GB")
        if usage > args.threshold:
            print(f"WARNING: Exceeds threshold of {args.threshold} GB")
            sys.exit(1)
        else:
            print("OK: Within threshold")
            sys.exit(0)
    
    # Default behavior: demonstrate monitoring
    logger.info("Memory Monitor Utility Started")
    logger.info(f"Threshold set to: {args.threshold} GB")
    
    # Simulate a check
    if check_memory_threshold():
        logger.warning("Threshold exceeded in demo mode.")
    else:
        logger.info("Threshold not exceeded in demo mode.")

if __name__ == "__main__":
    main()