"""
Sampling utilities for microbiome data analysis.

Provides functions for stratified random sampling to preserve
distribution characteristics of target variables.
"""

import pandas as pd
import numpy as np
from typing import Optional


def stratified_sample(
    df: pd.DataFrame,
    target_col: str,
    retain_ratio: float,
    seed: int = 42
) -> pd.DataFrame:
    """
    Perform stratified random sampling by quartiles of the target column.

    This function divides the target column into quartiles, then samples
    a proportional number of rows from each quartile to preserve the
    overall distribution of the target variable.

    Args:
        df: Input DataFrame.
        target_col: Name of the column to stratify by (must be numeric).
        retain_ratio: Fraction of rows to retain (0.0 to 1.0).
        seed: Random seed for reproducibility.

    Returns:
        A new DataFrame with stratified sample.

    Raises:
        ValueError: If retain_ratio is not between 0 and 1, or if target_col
                   is not numeric or does not exist in the DataFrame.
    """
    if not 0.0 <= retain_ratio <= 1.0:
        raise ValueError("retain_ratio must be between 0.0 and 1.0")

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame")

    if not pd.api.types.is_numeric_dtype(df[target_col]):
        raise ValueError(f"Target column '{target_col}' must be numeric")

    # Handle empty DataFrame
    if df.empty:
        return df.copy()

    # Set random seed
    rng = np.random.default_rng(seed)

    # Calculate quartile boundaries
    quartiles = df[target_col].quantile([0.25, 0.5, 0.75])
    q1, q2, q3 = quartiles.values

    # Define bins for stratification
    # We create 4 bins: (-inf, q1], (q1, q2], (q2, q3], (q3, inf]
    bins = [-np.inf, q1, q2, q3, np.inf]
    labels = ['q1', 'q2', 'q3', 'q4']

    # Assign each row to a quartile bin
    df_with_quartiles = df.copy()
    df_with_quartiles['_quartile'] = pd.cut(
        df_with_quartiles[target_col],
        bins=bins,
        labels=labels,
        include_lowest=True
    )

    # Sample from each quartile proportionally
    sampled_rows = []
    for label in labels:
        quartile_df = df_with_quartiles[df_with_quartiles['_quartile'] == label]
        if len(quartile_df) == 0:
            continue

        # Calculate number of rows to keep from this quartile
        n_to_keep = max(1, int(len(quartile_df) * retain_ratio))

        # Sample without replacement
        if n_to_keep >= len(quartile_df):
            sampled_quartile = quartile_df
        else:
            sampled_quartile = quartile_df.sample(
                n=n_to_keep,
                random_state=rng.integers(0, 2**31)
            )

        sampled_rows.append(sampled_quartile)

    # Combine sampled rows
    if not sampled_rows:
        return df.copy()

    result = pd.concat(sampled_rows, ignore_index=True)

    # Drop the temporary quartile column
    result = result.drop(columns=['_quartile'])

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
        retain_ratio: Fraction of rows to retain (0.0 to 1.0).
        seed: Random seed for reproducibility.

    Returns:
        A new DataFrame with random sample.
    """
    if not 0.0 <= retain_ratio <= 1.0:
        raise ValueError("retain_ratio must be between 0.0 and 1.0")

    if df.empty:
        return df.copy()

    rng = np.random.default_rng(seed)
    n_to_keep = max(1, int(len(df) * retain_ratio))

    if n_to_keep >= len(df):
        return df.copy()

    return df.sample(
        n=n_to_keep,
        random_state=rng.integers(0, 2**31)
    )
