"""
Memory monitoring utilities for the llmXive statistical power analysis pipeline.

This module provides functionality to track RAM usage and trigger downsampling
strategies if memory consumption exceeds the defined threshold (FR-006).
"""

import gc
import logging
import os
import sys
from typing import Callable, Optional, Dict, Any

import psutil

# Configuration constants
MEMORY_THRESHOLD_GB = 6.0
MEMORY_THRESHOLD_BYTES = MEMORY_THRESHOLD_GB * 1024**3

logger = logging.getLogger(__name__)


def get_current_memory_usage_gb() -> float:
    """
    Get the current memory usage of the current process in gigabytes.

    Returns:
        float: Memory usage in GB.
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / (1024**3)


def check_memory_threshold(threshold_gb: float = MEMORY_THRESHOLD_GB) -> bool:
    """
    Check if current memory usage exceeds the specified threshold.

    Args:
        threshold_gb: The memory threshold in GB (default: 6.0 GB).

    Returns:
        bool: True if usage exceeds threshold, False otherwise.
    """
    current_usage = get_current_memory_usage_gb()
    logger.debug(f"Current memory usage: {current_usage:.2f} GB")
    return current_usage > threshold_gb


def trigger_gc() -> int:
    """
    Force garbage collection to reclaim memory.

    Returns:
        int: The number of objects collected (approximate).
    """
    logger.info("Triggering garbage collection to reclaim memory.")
    collected = gc.collect()
    logger.info(f"Garbage collection complete. Collected {collected} objects.")
    return collected


def downsample_data(
    data_iterator: Callable,
    target_fraction: float = 0.5,
    **kwargs
) -> Any:
    """
    A generic downsampling strategy that reduces data volume by a target fraction.

    Since the specific data structure is not known at this utility level,
    this function assumes the input `data_iterator` is a callable that returns
    a dataset object (e.g., a list, numpy array, or pandas DataFrame) when called,
    or an iterable that can be sliced.

    This is a placeholder for the actual downsampling logic which will be
    implemented in the data loading or preprocessing stages.

    Args:
        data_iterator: A callable or iterable representing the data to be downsized.
        target_fraction: The fraction of data to keep (0.0 to 1.0).
        **kwargs: Additional arguments passed to the downsampling logic.

    Returns:
        The downsized data object.

    Raises:
        NotImplementedError: If the specific data type is not handled.
        ValueError: If target_fraction is invalid.
    """
    if not (0.0 < target_fraction <= 1.0):
        raise ValueError("target_fraction must be between 0.0 (exclusive) and 1.0 (inclusive).")

    logger.warning(f"Memory threshold exceeded. Initiating downsampling to {target_fraction * 100:.0f}% of original size.")

    # Note: In a real implementation, this would inspect the type of data
    # and perform specific slicing (e.g., df.sample(frac=...) or arr[::step]).
    # For now, we raise a NotImplementedError to force the caller to implement
    # specific logic for their data type, or we provide a generic fallback
    # if the data supports standard slicing.

    if callable(data_iterator):
        try:
            data = data_iterator()
        except Exception as e:
            logger.error(f"Failed to retrieve data for downsampling: {e}")
            raise
    else:
        data = data_iterator

    # Attempt generic downsampling if it supports slicing and len
    if hasattr(data, '__len__') and hasattr(data, '__getitem__'):
        new_length = int(len(data) * target_fraction)
        logger.info(f"Downsampling data from {len(data)} to {new_length} items.")
        # Simple slice for lists/arrays; pandas/numpy usually handle this better
        # but we assume a generic indexable structure here.
        return data[:new_length]
    else:
        raise NotImplementedError(
            f"Automatic downsampling not implemented for type {type(data)}. "
            "Please implement specific downsampling logic for this data type."
        )


def monitor_and_ensure_memory(
    check_func: Optional[Callable[[], None]] = None,
    threshold_gb: float = MEMORY_THRESHOLD_GB,
    downsampling_strategy: Optional[Callable] = None
) -> bool:
    """
    Monitor memory usage and trigger actions if the threshold is exceeded.

    This function is designed to be called periodically during data processing.

    Args:
        check_func: An optional callback to perform custom checks or data retrieval
                    if downsampling is needed.
        threshold_gb: The memory threshold in GB.
        downsampling_strategy: An optional callable to handle downsampling.
                               If None, a default strategy is attempted.

    Returns:
        bool: True if memory is within limits (or successfully reduced),
              False if memory is critical and could not be resolved.
    """
    if check_memory_threshold(threshold_gb):
        logger.warning(f"Memory usage ({get_current_memory_usage_gb():.2f} GB) exceeds threshold ({threshold_gb} GB).")

        # Step 1: Force Garbage Collection
        trigger_gc()

        # Step 2: Re-check
        if check_memory_threshold(threshold_gb):
            logger.warning("Memory still exceeds threshold after GC. Attempting downsampling.")

            if downsampling_strategy:
                try:
                    downsampling_strategy()
                except Exception as e:
                    logger.error(f"Downsampling strategy failed: {e}")
                    # Fail loudly as per FR-006 requirement for robust handling
                    # If we cannot reduce memory, the pipeline should not continue
                    # with potentially unstable memory conditions.
                    return False
            else:
                logger.error("Memory threshold exceeded and no downsampling strategy provided. Aborting.")
                return False

            # Step 3: Final Check
            if check_memory_threshold(threshold_gb):
                logger.error(f"Memory usage ({get_current_memory_usage_gb():.2f} GB) still exceeds threshold after downsampling. Aborting.")
                return False
            else:
                logger.info("Memory usage reduced successfully.")
                return True
        else:
            logger.info("Memory usage recovered after garbage collection.")
            return True

    return True


def main():
    """
    Command-line interface for testing the memory monitor.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting memory monitor test.")
    logger.info(f"Current memory usage: {get_current_memory_usage_gb():.2f} GB")
    logger.info(f"Threshold set to: {MEMORY_THRESHOLD_GB} GB")

    is_safe = monitor_and_ensure_memory()
    if is_safe:
        logger.info("Memory check passed.")
        sys.exit(0)
    else:
        logger.error("Memory check failed. Critical memory conditions detected.")
        sys.exit(1)


if __name__ == "__main__":
    main()
