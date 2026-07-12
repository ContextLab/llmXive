"""
metrics.py - Calibration and Covariate Shift Metrics

Implements:
- Expected Calibration Error (ECE)
- Brier Score
- PCA-based Covariate Shift
- Key Feature Mean Shift
- Spearman Correlation
"""

import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import brier_score_loss
from scipy.stats import spearmanr
from typing import List, Optional, Tuple, Union, Dict, Any
import logging

logger = logging.getLogger(__name__)


def expected_calibration_error(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10
) -> float:
    """
    Calculate Expected Calibration Error (ECE) with specified number of bins.

    Args:
        y_true: True binary labels (0 or 1)
        y_prob: Predicted probabilities for the positive class
        n_bins: Number of bins for calibration (default 10)

    Returns:
        ECE value as a float
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    # Bin boundaries
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total_samples = len(y_true)

    for i in range(n_bins):
        # Define bin range
        lower = bin_boundaries[i]
        upper = bin_boundaries[i + 1]

        # Identify samples in this bin
        if i == n_bins - 1:
            # Include right edge for the last bin
            in_bin = (y_prob >= lower) & (y_prob <= upper)
        else:
            in_bin = (y_prob >= lower) & (y_prob < upper)

        bin_size = np.sum(in_bin)

        if bin_size > 0:
            # Average predicted probability in the bin
            avg_confidence = np.mean(y_prob[in_bin])
            # Actual accuracy (fraction of positives) in the bin
            avg_accuracy = np.mean(y_true[in_bin])
            # Weighted absolute difference
            ece += (bin_size / total_samples) * np.abs(avg_accuracy - avg_confidence)

    return float(ece)


def brier_score(
    y_true: np.ndarray,
    y_prob: np.ndarray
) -> float:
    """
    Calculate Brier Score (Mean Squared Error of probabilities).

    Args:
        y_true: True binary labels
        y_prob: Predicted probabilities

    Returns:
        Brier Score as a float
    """
    return float(brier_score_loss(y_true, y_prob))


def pca_shift(
    train_features: np.ndarray,
    test_features: np.ndarray,
    n_components: Union[int, float] = 0.95
) -> float:
    """
    Calculate PCA-based covariate shift.

    This method projects both train and test features onto the principal
    components of the training data, then computes the Euclidean distance
    between the mean projections.

    Formula:
    1. Fit PCA on train_features
    2. Project train_features and test_features onto the same components
    3. Compute Euclidean distance between mean(train_projected) and mean(test_projected)

    Args:
        train_features: Training feature matrix (n_samples, n_features)
        test_features: Test feature matrix (n_samples, n_features)
        n_components: Number of components or variance threshold (default 0.95)

    Returns:
        PCA shift value (Euclidean distance between mean projections)
    """
    train_features = np.asarray(train_features)
    test_features = np.asarray(test_features)

    if train_features.shape[1] != test_features.shape[1]:
        raise ValueError(
            f"Feature dimension mismatch: train={train_features.shape[1]}, "
            f"test={test_features.shape[1]}"
        )

    # Handle edge case of single feature or zero variance
    if train_features.shape[1] == 0:
        return 0.0

    # Initialize PCA
    # If n_components is a float, it represents variance ratio
    # If int, it represents number of components
    try:
        pca = PCA(n_components=n_components)
        pca.fit(train_features)
    except ValueError as e:
        # Fallback if variance threshold is too high for data rank
        logger.warning(f"PCA variance threshold {n_components} too high, using min(n_features, n_samples): {e}")
        n_comp = min(train_features.shape[0], train_features.shape[1], train_features.shape[1])
        if n_comp <= 0:
            return 0.0
        pca = PCA(n_components=n_comp)
        pca.fit(train_features)

    # Transform both sets
    train_proj = pca.transform(train_features)
    test_proj = pca.transform(test_features)

    # Compute means
    train_mean = np.mean(train_proj, axis=0)
    test_mean = np.mean(test_proj, axis=0)

    # Euclidean distance between means
    shift = np.linalg.norm(test_mean - train_mean)

    return float(shift)


def key_feature_shift(
    train_features: np.ndarray,
    test_features: np.ndarray,
    feature_names: Optional[List[str]] = None,
    key_features: Optional[List[int]] = None
) -> float:
    """
    Calculate Key Feature Mean Shift.

    This computes the mean shift for specific key features. If no specific
    features are provided, it defaults to the first 5 features (or all if fewer).
    Alternatively, if feature_names are provided, it can identify key features
    by index.

    Formula:
    For each key feature j:
      shift_j = |mean(train_j) - mean(test_j)|
    Final metric = mean(shift_j) for all key features

    Args:
        train_features: Training feature matrix (n_samples, n_features)
        test_features: Test feature matrix (n_samples, n_features)
        feature_names: Optional list of feature names (for logging)
        key_features: Optional list of column indices to treat as "key" features.
                     If None, defaults to first 5 features.

    Returns:
        Average mean shift across key features
    """
    train_features = np.asarray(train_features)
    test_features = np.asarray(test_features)

    if train_features.shape[1] != test_features.shape[1]:
        raise ValueError(
            f"Feature dimension mismatch: train={train_features.shape[1]}, "
            f"test={test_features.shape[1]}"
        )

    n_features = train_features.shape[1]

    if n_features == 0:
        return 0.0

    # Determine key features
    if key_features is not None:
        # Validate indices
        key_features = [i for i in key_features if 0 <= i < n_features]
        if not key_features:
            logger.warning("No valid key features provided. Using all features.")
            key_features = list(range(n_features))
    else:
        # Default to first 5 features
        key_features = list(range(min(5, n_features)))

    shifts = []
    for idx in key_features:
        train_mean = np.mean(train_features[:, idx])
        test_mean = np.mean(test_features[:, idx])
        shift = abs(train_mean - test_mean)
        shifts.append(shift)

    avg_shift = float(np.mean(shifts))

    if feature_names and len(feature_names) >= n_features:
        key_names = [feature_names[i] for i in key_features if i < len(feature_names)]
        logger.debug(f"Key Feature Shift computed on: {key_names}")

    return avg_shift


def spearman_correlation(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation and p-value.

    Args:
        x: First array of values
        y: Second array of values

    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    x = np.asarray(x)
    y = np.asarray(y)

    if len(x) != len(y):
        raise ValueError(f"Array lengths must match: x={len(x)}, y={len(y)}")

    if len(x) < 2:
        return 0.0, 1.0

    rho, p_value = spearmanr(x, y)

    # Handle NaN results (e.g., constant input)
    if np.isnan(rho):
        rho = 0.0
    if np.isnan(p_value):
        p_value = 1.0

    return float(rho), float(p_value)