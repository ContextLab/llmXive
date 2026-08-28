"""
Data splitting utilities for molecular permeability datasets.

Implements stratified and random splitting strategies with strict validation
for polymer type stratification as required by FR-003.
"""

import logging
from typing import List, Tuple, Optional
import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


def random_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a simple random split of the dataframe.

    Args:
        df: Input dataframe containing molecular data.
        test_size: Proportion of the dataset to include in the test split.
        random_state: Seed for reproducibility.

    Returns:
        Tuple of (train_df, test_df).
    """
    if test_size <= 0 or test_size >= 1:
        raise ValueError("test_size must be between 0 and 1 (exclusive).")
    
    train_df, test_df = train_test_split(
        df, 
        test_size=test_size, 
        random_state=random_state, 
        shuffle=True
    )
    
    logger.info(f"Random split completed: Train={len(train_df)}, Test={len(test_df)}")
    return train_df, test_df


def stratified_split(
    df: pd.DataFrame,
    stratify_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
    max_distribution_diff: float = 0.05
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified split ensuring distribution difference < threshold.
    
    This function enforces FR-003 by requiring the stratification column to exist
    and validating that the distribution difference between train and test sets
    does not exceed the specified threshold (default 5%).

    Args:
        df: Input dataframe.
        stratify_col: Column name to stratify by (e.g., 'polymer_type').
        test_size: Proportion of the dataset for the test split.
        random_state: Random seed for reproducibility.
        max_distribution_diff: Maximum allowed absolute percentage point difference
                             in class distribution between train and test sets.

    Returns:
        Tuple of (train_df, test_df).

    Raises:
        SystemExit: If the stratification column is missing or if the distribution
                    difference exceeds the threshold after splitting.
        ValueError: If the stratification column has insufficient unique values.
    """
    if stratify_col not in df.columns:
        logger.error(
            f"Stratification column '{stratify_col}' not found in dataframe. "
            f"Available columns: {list(df.columns)}"
        )
        raise SystemExit(
            f"Stratification by {stratify_col} required by FR-003. "
            f"Dataset lacks this metadata."
        )

    if df[stratify_col].isna().any():
        logger.warning(f"Found NaN values in stratification column '{stratify_col}'. Dropping rows.")
        df = df.dropna(subset=[stratify_col])

    if df[stratify_col].nunique() < 2:
        logger.error(f"Stratification column '{stratify_col}' has fewer than 2 unique classes.")
        raise ValueError(
            f"Cannot stratify by '{stratify_col}': only {df[stratify_col].nunique()} unique class found."
        )

    try:
        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=df[stratify_col],
            shuffle=True
        )
    except ValueError as e:
        # Handle cases where stratification fails due to small class sizes
        logger.error(f"Stratified split failed: {e}")
        raise SystemExit(
            f"Stratified split failed. Ensure each class in '{stratify_col}' has sufficient samples "
            f"to support a {test_size*100:.0f}% test split."
        )

    # Validate distribution difference
    train_dist = train_df[stratify_col].value_counts(normalize=True).sort_index()
    test_dist = test_df[stratify_col].value_counts(normalize=True).sort_index()
    
    # Align indices to handle missing classes in one split (though unlikely with stratify)
    all_classes = train_dist.index.union(test_dist.index)
    train_dist = train_dist.reindex(all_classes, fill_value=0)
    test_dist = test_dist.reindex(all_classes, fill_value=0)

    diff = (train_dist - test_dist).abs()
    max_diff = diff.max()

    logger.info(f"Stratification column: {stratify_col}")
    logger.info(f"Train distribution:\n{train_dist}")
    logger.info(f"Test distribution:\n{test_dist}")
    logger.info(f"Max distribution difference: {max_diff:.4f} (threshold: {max_distribution_diff})")

    if max_diff > max_distribution_diff:
        logger.error(
            f"Stratification failed: Max distribution difference ({max_diff:.4f}) exceeds "
            f"threshold ({max_distribution_diff})."
        )
        raise SystemExit(
            f"Stratification validation failed. Distribution difference ({max_diff:.4f}) "
            f"exceeds allowed threshold ({max_distribution_diff}). "
            f"Consider adjusting test_size or checking dataset balance."
        )

    logger.info(f"Stratified split successful: Train={len(train_df)}, Test={len(test_df)}")
    return train_df, test_df