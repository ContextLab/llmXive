"""
Sampling utilities for the microbiome study pipeline.

Provides stratified sampling functions to preserve distributional properties
of target variables during dataset reduction.
"""
import pandas as pd
import numpy as np
from typing import Optional


def stratified_sample(
    df: pd.DataFrame,
    target_col: str,
    retain_ratio: float,
    seed: int = 42,
    n_bins: int = 4
) -> pd.DataFrame:
    """
    Perform stratified random sampling by quartiles of the target column.

    This ensures that the distribution of the target variable is preserved
    in the sampled subset, which is critical for maintaining statistical
    power in downstream analyses.

    Args:
        df: Input DataFrame.
        target_col: Name of the column to stratify by (e.g., 'log_titer').
        retain_ratio: Fraction of data to retain (0.0 to 1.0).
        seed: Random seed for reproducibility.
        n_bins: Number of strata (bins) to create. Default is 4 (quartiles).

    Returns:
        A new DataFrame containing the stratified sample.

    Raises:
        ValueError: If retain_ratio is not between 0 and 1.
        ValueError: If target_col is not in the DataFrame.
        ValueError: If the target column contains non-numeric data or NaNs.
    """
    if not 0.0 <= retain_ratio <= 1.0:
        raise ValueError(f"retain_ratio must be between 0 and 1, got {retain_ratio}")

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame. "
                         f"Available columns: {list(df.columns)}")

    # Ensure target column is numeric and handle NaNs
    if not pd.api.types.is_numeric_dtype(df[target_col]):
        raise ValueError(f"Target column '{target_col}' must be numeric.")

    if df[target_col].isna().any():
        raise ValueError(f"Target column '{target_col}' contains NaN values. "
                         "Please handle missing values before sampling.")

    # Create a copy to avoid modifying the original
    df_sample = df.copy()

    # Set random seed
    np.random.seed(seed)

    # Create stratification bins using qcut (quantiles)
    # This ensures equal-sized bins based on the data distribution
    try:
        # Create bins based on quantiles
        df_sample['_stratum'] = pd.qcut(df_sample[target_col], q=n_bins, duplicates='drop')
    except ValueError as e:
        # If qcut fails (e.g., too few unique values), fall back to uniform bins
        min_val = df_sample[target_col].min()
        max_val = df_sample[target_col].max()
        df_sample['_stratum'] = pd.cut(df_sample[target_col], 
                                       bins=n_bins, 
                                       range=(min_val, max_val))

    # Perform stratified sampling
    sampled_indices = []
    for stratum in df_sample['_stratum'].unique():
        stratum_df = df_sample[df_sample['_stratum'] == stratum]
        n_to_sample = max(1, int(len(stratum_df) * retain_ratio))
        
        # Sample without replacement
        if n_to_sample >= len(stratum_df):
            sampled_indices.extend(stratum_df.index.tolist())
        else:
            sampled_indices.extend(stratum_df.sample(n=n_to_sample, random_state=seed).index.tolist())

    # Drop the temporary stratum column and return
    result = df_sample.loc[sampled_indices].drop(columns=['_stratum'])
    
    # Reset index for cleanliness
    result = result.reset_index(drop=True)
    
    return result


def simple_random_sample(
    df: pd.DataFrame,
    retain_ratio: float,
    seed: int = 42
) -> pd.DataFrame:
    """
    Perform simple random sampling without stratification.

    Args:
        df: Input DataFrame.
        retain_ratio: Fraction of data to retain (0.0 to 1.0).
        seed: Random seed for reproducibility.

    Returns:
        A new DataFrame containing the random sample.
    """
    if not 0.0 <= retain_ratio <= 1.0:
        raise ValueError(f"retain_ratio must be between 0 and 1, got {retain_ratio}")

    np.random.seed(seed)
    n_samples = max(1, int(len(df) * retain_ratio))
    
    # Sample without replacement
    sampled_df = df.sample(n=n_samples, random_state=seed).reset_index(drop=True)
    
    return sampled_df