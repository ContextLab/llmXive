"""
Sampling utility for stratified random sampling.

Provides functions to perform stratified sampling on dataframes
to preserve distribution characteristics while reducing dataset size.
"""
import logging
import numpy as np
import pandas as pd
from typing import Optional
from pathlib import Path

from .logging_config import get_logger

logger: logging.Logger = get_logger(__name__)


def stratified_sample(
    df: pd.DataFrame,
    target_col: str,
    retain_ratio: float,
    seed: int = 42
) -> pd.DataFrame:
    """
    Perform stratified random sampling by quartiles of the target column.
    
    This function preserves the distribution of the target variable by:
    1. Dividing the data into quartiles based on the target column
    2. Sampling a proportional number of rows from each quartile
    3. Returning the combined sample
    
    Args:
        df: Input DataFrame
        target_col: Column name to stratify by (should be numeric)
        retain_ratio: Fraction of data to retain (0.0 to 1.0)
        seed: Random seed for reproducibility
    
    Returns:
        Sampled DataFrame with approximately retain_ratio * len(df) rows
    
    Raises:
        ValueError: If retain_ratio is not between 0 and 1
        KeyError: If target_col is not in the DataFrame
        ValueError: If target_col contains non-numeric data
    """
    if not 0.0 <= retain_ratio <= 1.0:
        raise ValueError(f"retain_ratio must be between 0 and 1, got {retain_ratio}")
    
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' not found in DataFrame. Available columns: {list(df.columns)}")
    
    if not pd.api.types.is_numeric_dtype(df[target_col]):
        raise ValueError(f"Target column '{target_col}' must be numeric, got {df[target_col].dtype}")
    
    # Handle NaN values in target column
    if df[target_col].isna().any():
        logger.warning(f"Found {df[target_col].isna().sum()} NaN values in '{target_col}'. Dropping these rows for stratification.")
        df = df.dropna(subset=[target_col])
    
    if len(df) == 0:
        logger.warning("DataFrame is empty after dropping NaN values. Returning empty DataFrame.")
        return df.reset_index(drop=True)
    
    # Set random seed for reproducibility
    np.random.seed(seed)
    
    # Create quartile bins
    df_with_q = df.copy()
    df_with_q['stratum'] = pd.qcut(df_with_q[target_col], q=4, duplicates='drop')
    
    # Calculate sample size per stratum
    stratum_counts = df_with_q.groupby('stratum').size()
    total_rows = len(df_with_q)
    target_sample_size = int(total_rows * retain_ratio)
    
    logger.info(f"Total rows: {total_rows}, Target sample size: {target_sample_size}")
    logger.info(f"Stratum distribution: {stratum_counts.to_dict()}")
    
    sampled_dfs = []
    
    for stratum, count in stratum_counts.items():
        # Calculate how many rows to sample from this stratum
        stratum_sample_size = int(count * retain_ratio)
        # Ensure at least 1 row per stratum if we're keeping any data
        if stratum_sample_size == 0 and target_sample_size > 0:
            stratum_sample_size = 1
        
        # Don't sample more than available
        stratum_sample_size = min(stratum_sample_size, count)
        
        # Sample from this stratum
        stratum_df = df_with_q[df_with_q['stratum'] == stratum]
        sampled_stratum = stratum_df.sample(n=stratum_sample_size, random_state=seed)
        sampled_dfs.append(sampled_stratum)
        logger.debug(f"Stratum {stratum}: sampled {stratum_sample_size}/{count} rows")
    
    # Combine sampled dataframes
    if not sampled_dfs:
        logger.warning("No data sampled. Returning empty DataFrame.")
        return df.reset_index(drop=True)
    
    sampled_df = pd.concat(sampled_dfs, ignore_index=True)
    
    # Drop the temporary stratum column
    sampled_df = sampled_df.drop(columns=['stratum'])
    
    # Shuffle the result
    sampled_df = sampled_df.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    logger.info(f"Final sample size: {len(sampled_df)} rows (target: {target_sample_size})")
    
    return sampled_df
