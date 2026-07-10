"""
Memory-safe subsampling utilities for the fungal community analysis pipeline.

Implements FR-009: Trigger subsampling if RAM usage exceeds 6GB.
"""
import os
import sys
import psutil
import logging
from typing import Tuple, Optional, List, Any
import pandas as pd
import numpy as np

# Configuration constants
RAM_LIMIT_GB = 6.0
RAM_LIMIT_BYTES = RAM_LIMIT_GB * 1024 ** 3
SUBSAMPLE_RATIO_DEFAULT = 0.5

logger = logging.getLogger(__name__)


def get_current_ram_usage_gb() -> float:
    """
    Returns the current RAM usage of the current process in GB.
    
    Returns:
        float: Current RAM usage in GB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)


def check_ram_and_subsample(
    data: pd.DataFrame,
    target_column: str,
    group_column: Optional[str] = None,
    min_samples_per_group: int = 10,
    force_ratio: Optional[float] = None
) -> Tuple[pd.DataFrame, float, bool]:
    """
    Checks current RAM usage and subsamples the data if usage exceeds the limit.
    
    This function implements the logic for FR-009. It checks the current RAM usage.
    If usage > 6GB, it performs stratified subsampling to reduce memory footprint.
    
    Args:
        data: The input DataFrame to potentially subsample.
        target_column: The column representing the primary data values (e.g., ASV counts).
        group_column: Optional column to stratify subsampling by (e.g., 'sample_id' or 'biome').
        min_samples_per_group: Minimum number of samples to keep per group if stratified.
        force_ratio: Optional ratio to force subsampling (0.0 to 1.0). If None, 
                     calculated dynamically if needed.
                     
    Returns:
        Tuple containing:
            - pd.DataFrame: The (potentially subsampled) data.
            - float: The subsampling ratio used (1.0 if no subsampling occurred).
            - bool: True if subsampling was performed, False otherwise.
    
    Raises:
        ValueError: If subsampling would result in fewer than min_samples_per_group.
    """
    current_ram = get_current_ram_usage_gb()
    
    if current_ram <= RAM_LIMIT_GB:
        logger.info(f"RAM usage ({current_ram:.2f} GB) is within limit ({RAM_LIMIT_GB} GB). No subsampling needed.")
        return data, 1.0, False

    logger.warning(f"RAM usage ({current_ram:.2f} GB) exceeds limit ({RAM_LIMIT_GB} GB). Triggering subsampling.")
    
    if force_ratio is None:
        # Estimate required ratio to get under 75% of the limit (safety margin)
        # This is a heuristic; actual memory usage depends on data types and operations.
        target_ram = RAM_LIMIT_GB * 0.75
        estimated_ratio = target_ram / current_ram
        force_ratio = max(0.1, min(0.9, estimated_ratio)) # Clamp between 10% and 90%
        
    logger.info(f"Calculated subsampling ratio: {force_ratio:.2f}")

    if group_column and group_column in data.columns:
        # Stratified subsampling
        groups = data.groupby(group_column)
        new_groups = []
        
        for name, group in groups:
            n_samples = len(group)
            n_keep = max(min_samples_per_group, int(n_samples * force_ratio))
            
            if n_keep >= n_samples:
                new_groups.append(group)
            else:
                sampled = group.sample(n=n_keep, random_state=42)
                new_groups.append(sampled)
        
        if not new_groups:
            raise ValueError("Subsampling resulted in an empty dataset.")
            
        result = pd.concat(new_groups, ignore_index=True)
    else:
        # Simple random subsampling
        n_keep = max(1, int(len(data) * force_ratio))
        result = data.sample(n=n_keep, random_state=42)

    actual_ratio = len(result) / len(data)
    logger.info(f"Subsampling complete. Rows: {len(data)} -> {len(result)} (ratio: {actual_ratio:.2f})")
    
    return result, actual_ratio, True


def estimate_dataframe_memory_mb(df: pd.DataFrame) -> float:
    """
    Estimates the memory usage of a DataFrame in MB.
    
    Args:
        df: The DataFrame to estimate.
        
    Returns:
        float: Estimated memory usage in MB.
    """
    return df.memory_usage(deep=True).sum() / (1024 ** 2)


def get_project_ram_limit() -> float:
    """
    Returns the RAM limit in GB defined for the project (default 6GB).
    
    Returns:
        float: RAM limit in GB.
    """
    return RAM_LIMIT_GB
