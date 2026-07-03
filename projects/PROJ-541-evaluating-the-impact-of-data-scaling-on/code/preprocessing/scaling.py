"""
Scaling functions for User Story 2: Scaling Application and Statistical Testing Pipeline.

Implements:
- standardize_data (T019): Z-score standardization (mean=0, std=1)
- min_max_scale (T020): Min-Max scaling (range=[0, 1])
- robust_scale (T021): Robust scaling using median and IQR
"""
import numpy as np
import logging
from typing import Union
import pandas as pd

# Get logger instance
logger = logging.getLogger(__name__)

def standardize_data(data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
    """
    Apply Z-score standardization to data.

    Transforms data to have zero mean and unit standard deviation.
    Formula: z = (x - mean) / std

    Args:
        data: Input data as numpy array or pandas DataFrame.

    Returns:
        Standardized numpy array with mean=0 and std=1 for each feature.

    Raises:
        ValueError: If input data is empty or has zero variance in a feature.
    """
    # Convert DataFrame to numpy if needed
    if isinstance(data, pd.DataFrame):
        data = data.values

    data = np.asarray(data, dtype=np.float64)

    if data.size == 0:
        raise ValueError("Input data cannot be empty")

    # Calculate mean and std for each feature (column)
    mean = np.mean(data, axis=0)
    std = np.std(data, axis=0, ddof=0)  # Population std

    # Handle zero variance (constant features)
    if np.any(std < 1e-10):
        logger.warning("Detected zero variance in one or more features. "
                     "These features will result in NaN after standardization.")

    # Apply standardization
    standardized = (data - mean) / std

    return standardized

def min_max_scale(data: Union[np.ndarray, pd.DataFrame], 
                  feature_range: tuple = (0.0, 1.0)) -> np.ndarray:
    """
    Apply Min-Max scaling to data.

    Transforms data to a specified range (default [0, 1]).
    Formula: x_scaled = (x - min) / (max - min) * (max_range - min_range) + min_range

    Args:
        data: Input data as numpy array or pandas DataFrame.
        feature_range: Target range (min, max). Default is (0, 1).

    Returns:
        Scaled numpy array with values in the specified range.

    Raises:
        ValueError: If input data is empty or has zero range in a feature.
    """
    # Convert DataFrame to numpy if needed
    if isinstance(data, pd.DataFrame):
        data = data.values

    data = np.asarray(data, dtype=np.float64)

    if data.size == 0:
        raise ValueError("Input data cannot be empty")

    min_range, max_range = feature_range

    # Calculate min and max for each feature
    min_val = np.min(data, axis=0)
    max_val = np.max(data, axis=0)

    # Handle zero range (constant features)
    range_val = max_val - min_val
    zero_range_mask = range_val < 1e-10

    if np.any(zero_range_mask):
        logger.warning(f"Detected zero range in {np.sum(zero_range_mask)} feature(s). "
                     "These features will be set to the minimum of the target range.")

    # Apply scaling
    # Avoid division by zero
    range_val_safe = np.where(zero_range_mask, 1.0, range_val)
    scaled = (data - min_val) / range_val_safe
    scaled = scaled * (max_range - min_range) + min_range

    # Set constant features to the minimum of the target range
    scaled[:, zero_range_mask] = min_range

    return scaled

def robust_scale(data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
    """
    Apply robust scaling using median and IQR.

    Transforms data using the median and interquartile range (IQR).
    Formula: x_scaled = (x - median) / IQR

    This scaling is robust to outliers.

    Args:
        data: Input data as numpy array or pandas DataFrame.

    Returns:
        Scaled numpy array with median=0 and IQR=1 for each feature.

    Raises:
        ValueError: If input data is empty.
    """
    # Convert DataFrame to numpy if needed
    if isinstance(data, pd.DataFrame):
        data = data.values

    data = np.asarray(data, dtype=np.float64)

    if data.size == 0:
        raise ValueError("Input data cannot be empty")

    # Calculate median and IQR for each feature
    median = np.median(data, axis=0)
    q75 = np.percentile(data, 75, axis=0)
    q25 = np.percentile(data, 25, axis=0)
    iqr = q75 - q25

    # Handle zero IQR (constant features)
    zero_iqr_mask = iqr < 1e-10

    if np.any(zero_iqr_mask):
        logger.warning(f"Detected zero IQR in {np.sum(zero_iqr_mask)} feature(s). "
                     "Skipping scaling for these features (setting to 0).")

    # Apply scaling
    iqr_safe = np.where(zero_iqr_mask, 1.0, iqr)
    scaled = (data - median) / iqr_safe

    # Set constant features to 0
    scaled[:, zero_iqr_mask] = 0.0

    return scaled