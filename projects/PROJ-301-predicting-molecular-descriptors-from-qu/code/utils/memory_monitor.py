import os
import gc
import sys
import logging
import resource
from typing import Callable, List, Optional, Tuple, Any, Dict
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

def get_memory_usage_bytes() -> int:
    """
    Get current memory usage in bytes.

    Returns:
        Memory usage in bytes.
    """
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024

def get_memory_usage_gb() -> float:
    """
    Get current memory usage in GB.

    Returns:
        Memory usage in GB.
    """
    return get_memory_usage_bytes() / (1024 ** 3)

def check_memory_limit(limit_gb: float = 6.5) -> bool:
    """
    Check if memory usage exceeds the limit.

    Args:
        limit_gb: Memory limit in GB.

    Returns:
        True if limit exceeded, False otherwise.
    """
    current_gb = get_memory_usage_gb()
    if current_gb > limit_gb:
        logger.warning(f"Memory usage {current_gb:.2f} GB exceeds limit {limit_gb} GB.")
        return True
    return False

def force_gc() -> None:
    """
    Force garbage collection.
    """
    gc.collect()

class MemoryMonitor:
    """
    A class to monitor memory usage and trigger downsampling if necessary.
    """

    def __init__(self, limit_gb: float = 6.5):
        """
        Initialize the MemoryMonitor.

        Args:
            limit_gb: Memory limit in GB.
        """
        self.limit_gb = limit_gb

    def get_memory_usage_gb(self) -> float:
        """
        Get current memory usage in GB.

        Returns:
            Memory usage in GB.
        """
        return get_memory_usage_gb()

    def check_memory_limit(self) -> bool:
        """
        Check if memory usage exceeds the limit.

        Returns:
            True if limit exceeded, False otherwise.
        """
        return check_memory_limit(self.limit_gb)

    def downsample_dataframe(
        self,
        df: pd.DataFrame,
        strata_columns: List[str],
        target_fraction: float = 0.5
    ) -> pd.DataFrame:
        """
        Downsample the DataFrame to meet memory limits.

        Args:
            df: DataFrame to downsample.
            strata_columns: Columns to use for stratified sampling.
            target_fraction: Fraction of data to keep.

        Returns:
            Downsampled DataFrame.
        """
        logger.info(f"Downsampling DataFrame to {target_fraction * 100}%...")
        if strata_columns:
            # Stratified sampling
            df_sample = df.groupby(strata_columns, group_keys=False).apply(
                lambda x: x.sample(frac=target_fraction, random_state=42)
            )
        else:
            # Random sampling
            df_sample = df.sample(frac=target_fraction, random_state=42)
        return df_sample.reset_index(drop=True)

def monitor_and_downsample(
    df: pd.DataFrame,
    limit_gb: float = 6.5,
    strata_columns: Optional[List[str]] = None,
    max_iterations: int = 10
) -> pd.DataFrame:
    """
    Monitor memory usage and downsample if necessary.

    Args:
        df: DataFrame to monitor.
        limit_gb: Memory limit in GB.
        strata_columns: Columns to use for stratified sampling.
        max_iterations: Maximum number of downsampling iterations.

    Returns:
        Downsampled DataFrame.
    """
    logger.info("Starting memory monitoring and downsampling...")
    monitor = MemoryMonitor(limit_gb)
    current_df = df
    iteration = 0

    while monitor.check_memory_limit() and iteration < max_iterations:
        logger.warning("Memory limit exceeded. Downsampling...")
        current_df = monitor.downsample_dataframe(current_df, strata_columns or [], target_fraction=0.8)
        iteration += 1

    if iteration == max_iterations:
        logger.warning("Reached maximum iterations. Memory limit may still be exceeded.")

    return current_df

def get_downsample_signal(memory_usage_gb: float, limit_gb: float) -> bool:
    """
    Get a signal to downsample based on memory usage.

    Args:
        memory_usage_gb: Current memory usage in GB.
        limit_gb: Memory limit in GB.

    Returns:
        True if downsampling is needed, False otherwise.
    """
    return memory_usage_gb > limit_gb

def configure_logging_for_pipeline() -> None:
    """
    Configure logging for the pipeline.
    """
    pass
