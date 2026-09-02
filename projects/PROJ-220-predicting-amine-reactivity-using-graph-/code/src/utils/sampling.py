"""
Dataset sampling utilities for handling large datasets within memory constraints.

Implements FR-008: Sampling strategy when dataset exceeds memory limits.
"""
import logging
import random
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def sample_dataset(
    dataset: Union[pd.DataFrame, List[Dict], np.ndarray],
    max_rows: Optional[int] = None,
    max_memory_mb: int = 7000,
    sampling_strategy: str = 'random',
    seed: int = 42
) -> Union[pd.DataFrame, List[Dict], np.ndarray]:
    """
    Sample a dataset to fit within memory constraints.
    
    Args:
        dataset: Input dataset (DataFrame, list of dicts, or numpy array)
        max_rows: Maximum number of rows to keep (if specified, overrides memory calculation)
        max_memory_mb: Maximum allowed memory in MB (default 7GB)
        sampling_strategy: Strategy to use ('random', 'stratified', 'first_n')
        seed: Random seed for reproducibility
        
    Returns:
        Sampled dataset
        
    Raises:
        ValueError: If sampling strategy is invalid
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Determine dataset type and size
    if isinstance(dataset, pd.DataFrame):
        total_rows = len(dataset)
        sample_func = sample_dataframe
    elif isinstance(dataset, list):
        total_rows = len(dataset)
        sample_func = sample_list
    elif isinstance(dataset, np.ndarray):
        total_rows = len(dataset)
        sample_func = sample_numpy
    else:
        raise ValueError(f"Unsupported dataset type: {type(dataset)}")
    
    logger.info(f"Dataset has {total_rows} rows, memory limit: {max_memory_mb}MB")
    
    # If max_rows is specified, use it directly
    if max_rows is not None:
        if max_rows >= total_rows:
            logger.info(f"max_rows ({max_rows}) >= total rows ({total_rows}), returning full dataset")
            return dataset
        
        logger.info(f"Sampling to {max_rows} rows using {sampling_strategy} strategy")
        return sample_func(dataset, max_rows, sampling_strategy)
    
    # Estimate memory usage and determine safe sample size
    try:
        if isinstance(dataset, pd.DataFrame):
            estimated_memory_mb = dataset.memory_usage(deep=True).sum() / (1024 * 1024)
        elif isinstance(dataset, list):
            # Rough estimate for list of dicts
            estimated_memory_mb = total_rows * 0.001  # ~1KB per record estimate
        else:
            estimated_memory_mb = dataset.nbytes / (1024 * 1024)
        
        logger.info(f"Estimated memory usage: {estimated_memory_mb:.1f}MB")
        
        if estimated_memory_mb <= max_memory_mb * 0.8:  # Keep 20% buffer
            logger.info("Dataset fits within memory limits, returning full dataset")
            return dataset
        
        # Calculate sample size to fit within memory
        sample_ratio = (max_memory_mb * 0.8) / estimated_memory_mb
        max_rows = max(1, int(total_rows * sample_ratio))
        
        logger.info(f"Dataset exceeds memory limits. Sampling to {max_rows} rows ({sample_ratio:.1%} of original)")
        
    except Exception as e:
        logger.warning(f"Could not estimate memory usage: {e}. Using default sampling.")
        max_rows = min(10000, total_rows)  # Default safe sample size
    
    return sample_func(dataset, max_rows, sampling_strategy)


def sample_dataframe(
    df: pd.DataFrame,
    max_rows: int,
    strategy: str = 'random'
) -> pd.DataFrame:
    """
    Sample a pandas DataFrame.
    
    Args:
        df: Input DataFrame
        max_rows: Maximum number of rows to keep
        strategy: Sampling strategy
        
    Returns:
        Sampled DataFrame
    """
    if strategy == 'random':
        return df.sample(n=max_rows, random_state=42)
    elif strategy == 'stratified':
        # For stratified sampling, we need a stratification column
        # Default to using the first categorical column if available
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            strat_col = categorical_cols[0]
            return df.groupby(strat_col, group_keys=False).apply(
                lambda x: x.sample(n=min(len(x), max_rows // df[strat_col].nunique()), random_state=42)
            )
        else:
            # Fall back to random if no categorical columns
            return df.sample(n=max_rows, random_state=42)
    elif strategy == 'first_n':
        return df.head(max_rows)
    else:
        raise ValueError(f"Invalid sampling strategy: {strategy}")


def sample_list(
    data: List[Dict],
    max_rows: int,
    strategy: str = 'random'
) -> List[Dict]:
    """
    Sample a list of dictionaries.
    
    Args:
        data: Input list
        max_rows: Maximum number of items to keep
        strategy: Sampling strategy
        
    Returns:
        Sampled list
    """
    if strategy == 'random':
        return random.sample(data, min(max_rows, len(data)))
    elif strategy == 'first_n':
        return data[:max_rows]
    else:
        raise ValueError(f"Invalid sampling strategy: {strategy}")


def sample_numpy(
    arr: np.ndarray,
    max_rows: int,
    strategy: str = 'random'
) -> np.ndarray:
    """
    Sample a numpy array.
    
    Args:
        arr: Input array
        max_rows: Maximum number of rows to keep
        strategy: Sampling strategy
        
    Returns:
        Sampled array
    """
    if strategy == 'random':
        indices = np.random.choice(len(arr), size=min(max_rows, len(arr)), replace=False)
        return arr[indices]
    elif strategy == 'first_n':
        return arr[:max_rows]
    else:
        raise ValueError(f"Invalid sampling strategy: {strategy}")


def calculate_safe_batch_size(
    estimated_record_size_mb: float,
    max_memory_mb: int = 7000,
    buffer_ratio: float = 0.7
) -> int:
    """
    Calculate a safe batch size given estimated record size and memory limits.
    
    Args:
        estimated_record_size_mb: Estimated size of one record in MB
        max_memory_mb: Maximum allowed memory in MB
        buffer_ratio: Ratio of memory to reserve for overhead (0.7 = 70%)
        
    Returns:
        Safe batch size
    """
    safe_memory = max_memory_mb * buffer_ratio
    batch_size = int(safe_memory / max(estimated_record_size_mb, 0.001))  # Avoid division by zero
    return max(1, batch_size)
