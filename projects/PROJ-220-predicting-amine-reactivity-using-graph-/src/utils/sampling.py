import logging
import random
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def sample_dataset(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    target_size: int,
    strategy: str = "random",
    seed: Optional[int] = None,
    scaffold_column: Optional[str] = None
) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Reduce dataset size if memory limits are exceeded.

    This function implements the sampling strategy required by FR-008.
    It logs the sampling strategy used for auditability.

    Args:
        data: The input dataset as a pandas DataFrame or list of dicts.
        target_size: The desired number of samples after downsampling.
        strategy: Sampling strategy. Options:
            - "random": Random sampling (default)
            - "stratified": Stratified sampling by scaffold_column (if provided)
            - "first": Take the first `target_size` records
        seed: Random seed for reproducibility.
        scaffold_column: Column name for scaffold-based stratification.

    Returns:
        A sampled version of the input data with `target_size` records.

    Raises:
        ValueError: If target_size is greater than the current dataset size.
        ValueError: If stratified sampling is requested without scaffold_column.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # Convert list of dicts to DataFrame for uniform handling
    if isinstance(data, list):
        df = pd.DataFrame(data)
        is_list = True
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
        is_list = False
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")

    current_size = len(df)

    if target_size >= current_size:
        logger.warning(
            f"Target size ({target_size}) is greater than or equal to "
            f"current dataset size ({current_size}). Returning original data."
        )
        return data

    logger.info(
        f"Sampling dataset from {current_size} to {target_size} records. "
        f"Strategy: {strategy}"
    )

    if strategy == "random":
        sampled_df = df.sample(n=target_size, random_state=seed)
    
    elif strategy == "first":
        sampled_df = df.head(target_size)
    
    elif strategy == "stratified":
        if scaffold_column is None:
            raise ValueError(
                "Stratified sampling requires 'scaffold_column' to be specified."
            )
        if scaffold_column not in df.columns:
            raise ValueError(
                f"Scaffold column '{scaffold_column}' not found in dataset. "
                f"Available columns: {list(df.columns)}"
            )
        
        # Ensure we don't sample more than the smallest group
        group_counts = df[scaffold_column].value_counts()
        min_group_size = group_counts.min()
        
        if min_group_size == 0:
            raise ValueError(
                "One or more scaffold groups are empty. Cannot perform stratified sampling."
            )
        
        # Calculate proportional sample size per group
        # Ensure at least 1 sample per group if possible
        group_sizes = {}
        remaining = target_size
        
        # First pass: allocate proportional
        for scaffold, count in group_counts.items():
            proportional = int(count * (target_size / current_size))
            # Ensure at least 1 if we have enough remaining
            if proportional == 0 and remaining > 0:
                proportional = 1
            group_sizes[scaffold] = min(proportional, count)
            remaining -= group_sizes[scaffold]
        
        # Second pass: distribute remaining to largest groups
        sorted_groups = group_counts.sort_values(ascending=False).index
        for scaffold in sorted_groups:
            if remaining <= 0:
                break
            current_sampled = group_sizes[scaffold]
            current_total = group_counts[scaffold]
            if current_sampled < current_total:
                group_sizes[scaffold] += 1
                remaining -= 1
        
        # Perform stratified sampling
        sampled_groups = []
        for scaffold, size in group_sizes.items():
            group_data = df[df[scaffold_column] == scaffold]
            if size > len(group_data):
                size = len(group_data)
            sampled_group = group_data.sample(n=size, random_state=seed)
            sampled_groups.append(sampled_group)
        
        sampled_df = pd.concat(sampled_groups, ignore_index=True)
    
    else:
        raise ValueError(f"Unknown sampling strategy: {strategy}")

    # Log sampling details
    logger.info(
        f"Sampling complete. Resulting dataset size: {len(sampled_df)}. "
        f"Strategy used: {strategy}"
    )
    
    # Convert back to original format if needed
    if is_list:
        return sampled_df.to_dict(orient="records")
    
    return sampled_df