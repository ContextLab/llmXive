"""
Sampling utilities for the microbiome-immune correlation pipeline.

Provides stratified sampling functions to preserve distribution properties
while reducing dataset size for memory-constrained environments.
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple

from code.utils.config import get_random_seed, get_processed_path

logger = logging.getLogger(__name__)


def stratified_sample(
    df: pd.DataFrame,
    target_col: str,
    retain_ratio: float,
    seed: int = 42
) -> pd.DataFrame:
    """
    Perform stratified random sampling by quartiles of a target column.

    This preserves the distribution of the target variable (e.g., titer)
    while reducing the dataset size.

    Args:
        df: Input DataFrame.
        target_col: Column name to stratify by (e.g., 'titer_post_log').
        retain_ratio: Fraction of data to retain (0.0 < ratio <= 1.0).
        seed: Random seed for reproducibility.

    Returns:
        A new DataFrame with stratified sample.

    Raises:
        ValueError: If retain_ratio is out of bounds or target_col missing.
        KeyError: If target_col not found in DataFrame.
    """
    if not 0.0 < retain_ratio <= 1.0:
        raise ValueError(f"retain_ratio must be in (0.0, 1.0], got {retain_ratio}")

    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' not found in DataFrame. "
                       f"Available columns: {list(df.columns)}")

    if len(df) == 0:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df.copy()

    # Set seed for reproducibility
    np.random.seed(seed)

    # Create a copy to avoid modifying the original
    df_sample = df.copy()

    # Add a temporary column for quartile assignment
    # We use 'qcut' to ensure equal-sized bins, handling ties by dropping some
    try:
        df_sample['_stratum'] = pd.qcut(
            df_sample[target_col],
            q=4,  # Quartiles
            labels=False,
            duplicates='drop'
        )
    except ValueError as e:
        # If qcut fails (e.g., too few unique values), use unique values as strata
        logger.warning(f"qcut failed ({e}), falling back to unique value stratification.")
        df_sample['_stratum'] = pd.factorize(df_sample[target_col])[0]

    # Group by stratum and sample
    sampled_indices = []
    for stratum_id, group in df_sample.groupby('_stratum'):
        n_stratum = len(group)
        n_sample = max(1, int(n_stratum * retain_ratio))

        # Shuffle and select
        indices = group.index.tolist()
        np.random.shuffle(indices)
        sampled_indices.extend(indices[:n_sample])

    # Sort indices to maintain original order
    sampled_indices.sort()
    result = df_sample.loc[sampled_indices].drop(columns=['_stratum'])

    logger.info(
        f"Stratified sampling: retained {len(result)} rows "
        f"({100 * retain_ratio:.1f}% of {len(df)}) "
        f"across {df_sample['_stratum'].nunique() if '_stratum' in df_sample.columns else 'N/A'} strata."
    )

    return result


def apply_memory_sampling(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    target_col: str = 'titer_post_log',
    retain_ratio: float = 0.8,
    seed: int = 42
) -> Tuple[pd.DataFrame, str]:
    """
    Apply stratified sampling to a dataset file, primarily for memory management.

    This function reads a CSV, performs stratified sampling, and writes the result.
    It is designed to be called when memory usage exceeds thresholds.

    Args:
        input_path: Path to input CSV. Defaults to processed path if None.
        output_path: Path to output CSV. Defaults to 'cleared_sampled.csv' in processed dir.
        target_col: Column to stratify by.
        retain_ratio: Fraction to retain.
        seed: Random seed.

    Returns:
        Tuple of (sampled DataFrame, path to output file).
    """
    if input_path is None:
        processed_dir = get_processed_path()
        input_path = processed_dir / 'cleared.csv'

    if output_path is None:
        processed_dir = get_processed_path()
        output_path = processed_dir / 'cleared_sampled.csv'

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path} for memory sampling...")
    df = pd.read_csv(input_path)

    logger.info(f"Applying stratified sampling (retain_ratio={retain_ratio})...")
    df_sampled = stratified_sample(
        df=df,
        target_col=target_col,
        retain_ratio=retain_ratio,
        seed=seed
    )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing sampled data to {output_path}")
    df_sampled.to_csv(output_path, index=False)

    return df_sampled, str(output_path)