"""
Utility functions for outlier exclusion based on sigma threshold.

This module implements the logic for identifying and excluding outliers
from the target variable distribution based on a configurable sigma threshold.
"""
import numpy as np
import pandas as pd
import logging
from typing import Tuple, List, Optional, Dict, Any
from code.config import SEED, OUTLIER_SIGMA

logger = logging.getLogger(__name__)

def identify_outliers(
    target_values: np.ndarray,
    threshold_sigma: float = OUTLIER_SIGMA,
    seed: int = SEED
) -> np.ndarray:
    """
    Identify outliers in the target variable based on a sigma threshold.
    
    Args:
        target_values: Array of target variable values (e.g., log-transformed conductivity)
        threshold_sigma: Number of standard deviations from the mean to consider as outlier
        seed: Random seed for reproducibility (used if any random sampling is needed)
    
    Returns:
        Boolean array where True indicates an outlier
    
    Raises:
        ValueError: If threshold_sigma is negative or target_values is empty
    """
    if len(target_values) == 0:
        raise ValueError("target_values cannot be empty")
    
    if threshold_sigma < 0:
        logger.warning(f"Negative threshold_sigma ({threshold_sigma}) detected. Using absolute value.")
        threshold_sigma = abs(threshold_sigma)
    
    mean_val = np.mean(target_values)
    std_val = np.std(target_values)
    
    if std_val == 0:
        logger.warning("Standard deviation is zero. No outliers will be detected.")
        return np.zeros(len(target_values), dtype=bool)
    
    lower_bound = mean_val - threshold_sigma * std_val
    upper_bound = mean_val + threshold_sigma * std_val
    
    outliers_mask = (target_values < lower_bound) | (target_values > upper_bound)
    
    logger.info(
        f"Outlier detection: mean={mean_val:.4f}, std={std_val:.4f}, "
        f"threshold={threshold_sigma}σ, bounds=[{lower_bound:.4f}, {upper_bound:.4f}], "
        f"outliers={np.sum(outliers_mask)}/{len(target_values)}"
    )
    
    return outliers_mask

def exclude_outliers(
    df: pd.DataFrame,
    target_col: str,
    threshold_sigma: float = OUTLIER_SIGMA,
    seed: int = SEED,
    return_mask: bool = False
) -> Tuple[pd.DataFrame, Optional[np.ndarray]]:
    """
    Exclude outliers from a DataFrame based on the target variable.
    
    Args:
        df: Input DataFrame
        target_col: Name of the target variable column
        threshold_sigma: Number of standard deviations from the mean to consider as outlier
        seed: Random seed for reproducibility
        return_mask: If True, also return the outlier mask array
    
    Returns:
        Tuple of (cleaned DataFrame, optional outlier mask array)
    
    Raises:
        KeyError: If target_col is not in DataFrame
        ValueError: If target_col contains non-numeric data
    """
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' not found in DataFrame")
    
    if not np.issubdtype(df[target_col].dtype, np.number):
        raise ValueError(f"Target column '{target_col}' must contain numeric data")
    
    target_values = df[target_col].values
    outliers_mask = identify_outliers(target_values, threshold_sigma, seed)
    
    cleaned_df = df[~outliers_mask].reset_index(drop=True)
    
    logger.info(
        f"Excluded {np.sum(outliers_mask)} outliers ({100*np.sum(outliers_mask)/len(df):.1f}% of data). "
        f"Remaining samples: {len(cleaned_df)}"
    )
    
    if return_mask:
        return cleaned_df, outliers_mask
    
    return cleaned_df, None

def get_outlier_statistics(
    target_values: np.ndarray,
    threshold_sigma: float = OUTLIER_SIGMA
) -> Dict[str, Any]:
    """
    Calculate statistics about outliers for reporting purposes.
    
    Args:
        target_values: Array of target variable values
        threshold_sigma: Number of standard deviations from the mean to consider as outlier
    
    Returns:
        Dictionary containing outlier statistics
    """
    mean_val = np.mean(target_values)
    std_val = np.std(target_values)
    min_val = np.min(target_values)
    max_val = np.max(target_values)
    
    outliers_mask = identify_outliers(target_values, threshold_sigma)
    n_outliers = np.sum(outliers_mask)
    n_total = len(target_values)
    outlier_ratio = n_outliers / n_total if n_total > 0 else 0.0
    
    if n_outliers > 0:
        outlier_values = target_values[outliers_mask]
        outlier_min = np.min(outlier_values)
        outlier_max = np.max(outlier_values)
        outlier_mean = np.mean(outlier_values)
    else:
        outlier_min = None
        outlier_max = None
        outlier_mean = None
    
    return {
        'mean': float(mean_val),
        'std': float(std_val),
        'min': float(min_val),
        'max': float(max_val),
        'threshold_sigma': threshold_sigma,
        'lower_bound': float(mean_val - threshold_sigma * std_val),
        'upper_bound': float(mean_val + threshold_sigma * std_val),
        'n_outliers': int(n_outliers),
        'n_total': int(n_total),
        'outlier_ratio': float(outlier_ratio),
        'outlier_min': float(outlier_min) if outlier_min is not None else None,
        'outlier_max': float(outlier_max) if outlier_max is not None else None,
        'outlier_mean': float(outlier_mean) if outlier_mean is not None else None
    }

def apply_threshold_filter(
    df: pd.DataFrame,
    target_col: str,
    thresholds: List[float] = None,
    seed: int = SEED
) -> Dict[float, Dict[str, Any]]:
    """
    Apply outlier exclusion with multiple thresholds and return statistics for each.
    
    Args:
        df: Input DataFrame
        target_col: Name of the target variable column
        thresholds: List of sigma thresholds to test (default: [1.0, 2.0, 3.0, 3.5])
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary mapping threshold to outlier statistics
    """
    if thresholds is None:
        thresholds = [1.0, 2.0, 3.0, 3.5]
    
    target_values = df[target_col].values
    results = {}
    
    for threshold in thresholds:
        stats = get_outlier_statistics(target_values, threshold)
        results[threshold] = stats
    
    return results