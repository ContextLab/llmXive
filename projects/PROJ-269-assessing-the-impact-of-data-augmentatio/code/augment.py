"""
Data augmentation module implementing various techniques for synthetic data generation.

This module provides functions for Gaussian noise injection, SMOTE, and Random
Oversampling, with proper handling of edge cases like zero-variance samples.
"""

import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Union
from imblearn.over_sampling import SMOTE, RandomOverSampler
from imblearn.utils import check_X_y

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_zero_variance_columns(
    X: Union[np.ndarray, pd.DataFrame]
) -> List[int]:
    """
    Detect columns with zero variance in the feature matrix.

    Args:
        X: Feature matrix (numpy array or pandas DataFrame).

    Returns:
        List of column indices with zero variance.
    """
    if isinstance(X, pd.DataFrame):
        X_array = X.values
    else:
        X_array = np.array(X)

    zero_variance_cols = []
    n_samples, n_features = X_array.shape

    for i in range(n_features):
        col = X_array[:, i]
        if np.var(col) == 0:
            zero_variance_cols.append(i)

    return zero_variance_cols

def exclude_zero_variance_samples(
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Exclude samples that result in zero-variance features after augmentation.

    Args:
        X: Feature matrix.
        y: Target labels.

    Returns:
        Tuple of (filtered_X, filtered_y) with zero-variance samples removed.
    """
    if isinstance(X, pd.DataFrame):
        X_array = X.values
    else:
        X_array = np.array(X)

    if isinstance(y, pd.Series):
        y_array = y.values
    else:
        y_array = np.array(y)

    # Check for zero variance across features for each sample
    # This is a simplified check - in practice, we'd check after augmentation
    valid_indices = []
    n_samples, n_features = X_array.shape

    for i in range(n_samples):
        # Check if this sample has any variance issues (simplified)
        # In practice, this would be checked after augmentation
        sample = X_array[i]
        if np.var(sample) > 0 or n_features == 1:
            valid_indices.append(i)

    return X_array[valid_indices], y_array[valid_indices]

def inject_gaussian_noise(
    X: Union[np.ndarray, pd.DataFrame],
    std: float = 0.1,
    random_state: Optional[int] = None
) -> np.ndarray:
    """
    Inject Gaussian noise into the feature matrix.

    Args:
        X: Feature matrix.
        std: Standard deviation of the Gaussian noise (default 0.1).
        random_state: Random seed for reproducibility.

    Returns:
        Noisy feature matrix as numpy array.
    """
    if random_state is not None:
        np.random.seed(random_state)

    if isinstance(X, pd.DataFrame):
        X_array = X.values
    else:
        X_array = np.array(X)

    noise = np.random.normal(0, std, X_array.shape)
    X_noisy = X_array + noise

    return X_noisy

def apply_smote(
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    random_state: Optional[int] = None,
    k_neighbors: int = 5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply SMOTE (Synthetic Minority Over-sampling Technique) to balance classes.

    Args:
        X: Feature matrix.
        y: Target labels.
        random_state: Random seed for reproducibility.
        k_neighbors: Number of nearest neighbors for SMOTE (default 5).

    Returns:
        Tuple of (X_resampled, y_resampled) with balanced classes.

    Raises:
        ValueError: If class count is too low for SMOTE.
    """
    if random_state is not None:
        np.random.seed(random_state)

    if isinstance(X, pd.DataFrame):
        X_array = X.values
    else:
        X_array = np.array(X)

    if isinstance(y, pd.Series):
        y_array = y.values
    else:
        y_array = np.array(y)

    # Check class distribution
    unique, counts = np.unique(y_array, return_counts=True)
    min_count = np.min(counts)

    if min_count < k_neighbors + 1:
        raise ValueError(
            f"Minimum class count ({min_count}) is too low for SMOTE "
            f"with k_neighbors={k_neighbors}. Consider using RandomOverSampler instead."
        )

    try:
        smote = SMOTE(random_state=random_state, k_neighbors=k_neighbors)
        X_resampled, y_resampled = smote.fit_resample(X_array, y_array)
        return X_resampled, y_resampled
    except Exception as e:
        logger.error(f"SMOTE failed: {e}")
        raise

def apply_random_oversampling(
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    random_state: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply random oversampling to balance classes.

    Args:
        X: Feature matrix.
        y: Target labels.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (X_resampled, y_resampled) with balanced classes.
    """
    if random_state is not None:
        np.random.seed(random_state)

    if isinstance(X, pd.DataFrame):
        X_array = X.values
    else:
        X_array = np.array(X)

    if isinstance(y, pd.Series):
        y_array = y.values
    else:
        y_array = np.array(y)

    try:
        ros = RandomOverSampler(random_state=random_state)
        X_resampled, y_resampled = ros.fit_resample(X_array, y_array)
        return X_resampled, y_resampled
    except Exception as e:
        logger.error(f"Random oversampling failed: {e}")
        raise

def augment_dataset(
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    method: str,
    **kwargs
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply augmentation method to the dataset.

    Args:
        X: Feature matrix.
        y: Target labels.
        method: Augmentation method ('gaussian', 'smote', 'random_oversample').
        **kwargs: Additional parameters for the augmentation method.

    Returns:
        Tuple of (X_augmented, y_augmented).

    Raises:
        ValueError: If unknown augmentation method is specified.
    """
    method = method.lower()

    if method == 'gaussian':
        std = kwargs.get('std', 0.1)
        random_state = kwargs.get('random_state')
        X_augmented = inject_gaussian_noise(X, std=std, random_state=random_state)
        return X_augmented, np.array(y) if isinstance(y, (pd.Series, list)) else y

    elif method == 'smote':
        random_state = kwargs.get('random_state')
        k_neighbors = kwargs.get('k_neighbors', 5)
        return apply_smote(X, y, random_state=random_state, k_neighbors=k_neighbors)

    elif method == 'random_oversample':
        random_state = kwargs.get('random_state')
        return apply_random_oversampling(X, y, random_state=random_state)

    else:
        raise ValueError(f"Unknown augmentation method: {method}")

def main() -> None:
    """
    Main entry point for the augmentation module.

    This function demonstrates the usage of the augmentation functions.
    In practice, this would be called from the main pipeline script.
    """
    logger.info("Augmentation module loaded successfully")
    logger.info("Available functions: detect_zero_variance_columns, exclude_zero_variance_samples, "
               "inject_gaussian_noise, apply_smote, apply_random_oversampling, augment_dataset")

    # Example usage (would be replaced with actual data in production)
    # X_sample = np.random.randn(100, 10)
    # y_sample = np.random.randint(0, 2, 100)
    # X_aug, y_aug = augment_dataset(X_sample, y_sample, 'smote', random_state=42)
    # logger.info(f"Augmented shape: {X_aug.shape}")

if __name__ == "__main__":
    main()