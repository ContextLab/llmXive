"""
Nested Cross-Validation utilities for ball milling impact prediction.

This module provides functions to generate stratified train/test splits
based on the target variable (D50), with a robust fallback mechanism
for cases where the target variable has insufficient unique values.
"""

import logging
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, KFold
from typing import List, Tuple, Optional, Generator

from src.utils.seed import get_seed

logger = logging.getLogger(__name__)

def generate_splits(
    df: pd.DataFrame,
    target_col: str = 'd50',
    n_splits: int = 5,
    n_repeats: int = 3,
    shuffle: bool = True,
    stratify: bool = True
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Generate stratified train/test splits for nested cross-validation.

    This function attempts to stratify splits based on the quantile-binned
    values of the target column (default: 'd50'). If stratification fails
    due to insufficient unique values (ties), it implements a fallback
    mechanism that reduces the number of bins (q) by half until a valid
    split is possible. If q=1 is reached, it logs a warning and falls back
    to a standard random split without stratification.

    Args:
        df: Input DataFrame containing the data.
        target_col: Name of the target column to stratify on (default: 'd50').
        n_splits: Number of splits (folds) for the outer loop (default: 5).
        n_repeats: Number of repeats for the repeated CV (default: 3).
        shuffle: Whether to shuffle the data before splitting (default: True).
        stratify: Whether to attempt stratification (default: True).

    Returns:
        A list of (train_idx, test_idx) tuples, where each is a numpy array
        of indices. The list length is n_splits * n_repeats.

    Raises:
        ValueError: If the target column is missing or contains only NaN values.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")

    target_values = df[target_col].dropna()
    if len(target_values) == 0:
        raise ValueError(f"Target column '{target_col}' contains no valid values.")

    seed = get_seed()
    splits = []

    # Determine the starting number of bins for quantile binning
    # We aim for 10 bins initially, but must ensure we don't exceed unique values
    max_q = min(10, len(target_values.unique()))
    
    if not stratify:
        logger.warning("Stratification explicitly disabled. Using random splits.")
        # Use standard KFold without stratification
        for _ in range(n_repeats):
            kf = KFold(n_splits=n_splits, shuffle=shuffle, random_state=seed)
            for train_idx, test_idx in kf.split(df):
                splits.append((train_idx, test_idx))
        return splits

    # Fallback mechanism for qcut
    q_values = []
    q = max_q
    while q > 1:
        q_values.append(q)
        if q <= 2:
            break
        q = q // 2
    
    # Ensure we try 10, 5, 2, and finally 1 (which triggers the random split)
    # If max_q was already small, we adjust the list
    if max_q < 10:
        # If we started with less than 10, we just try what we can
        q_values = [max_q]
        if max_q > 1:
            q_values.append(max_q // 2)
            if max_q // 2 > 1:
                 q_values.append(1) # Force the check for q=1 logic later

    # Sort q_values descending to try largest bins first
    q_values = sorted(list(set(q_values)), reverse=True)
    if 1 not in q_values:
        q_values.append(1)

    stratification_failed = False
    used_q = None

    for q in q_values:
        try:
            if q == 1:
                # This is the fallback to random split
                logger.warning("Stratification disabled: insufficient unique values")
                for _ in range(n_repeats):
                    kf = KFold(n_splits=n_splits, shuffle=shuffle, random_state=seed)
                    for train_idx, test_idx in kf.split(df):
                        splits.append((train_idx, test_idx))
                stratification_failed = True
                break

            # Attempt quantile binning
            # Use 'drop' to handle ties in a way that qcut might accept, 
            # but primarily rely on the reduction of q
            # We use duplicates='drop' to ensure we don't get an error if bins are empty
            # However, qcut raises ValueError if not enough unique values for q bins
            try:
                bins = pd.qcut(df[target_col], q=q, duplicates='drop')
            except ValueError:
                # If qcut still fails even with duplicates='drop', try reducing q further
                # This handles edge cases where unique values are fewer than q
                logger.debug(f"qcut failed with q={q}, trying next smaller bin count.")
                continue

            # Check if we actually got enough unique bins to stratify meaningfully
            if bins.nunique() < 2:
                logger.debug(f"qcut resulted in only {bins.nunique()} unique bins, insufficient for stratification.")
                continue

            # Success: we have valid bins
            used_q = q
            logger.info(f"Successfully generated stratified splits using q={used_q} bins.")
            
            for _ in range(n_repeats):
                skf = StratifiedKFold(n_splits=n_splits, shuffle=shuffle, random_state=seed)
                for train_idx, test_idx in skf.split(df, bins):
                    splits.append((train_idx, test_idx))
            break

        except Exception as e:
            logger.debug(f"Attempt with q={q} failed: {e}")
            continue

    if not stratification_failed and used_q is None:
        # If we exhausted all q values and didn't break out with success or q=1 logic
        # This implies we couldn't stratify at all, even with q=1 logic if it wasn't reached
        # But our loop ensures q=1 is always tried last.
        # If we are here, it means the loop finished without breaking.
        # This should technically be caught by the q=1 block above.
        # Just in case, fallback to random.
        logger.warning("Could not generate any stratified splits. Falling back to random splits.")
        for _ in range(n_repeats):
            kf = KFold(n_splits=n_splits, shuffle=shuffle, random_state=seed)
            for train_idx, test_idx in kf.split(df):
                splits.append((train_idx, test_idx))

    return splits
