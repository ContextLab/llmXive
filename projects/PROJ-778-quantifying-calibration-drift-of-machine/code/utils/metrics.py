"""
Metrics Utilities for Calibration Drift Analysis.

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
    Calculate Expected Calibration Error (ECE).
    
    Args:
        y_true: True binary labels (0 or 1).
        y_prob: Predicted probabilities.
        n_bins: Number of bins for calibration.
    
    Returns:
        ECE value.
    """
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        # Identify samples in this bin
        in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
        
        # For the first bin, include the lower boundary
        if i == 0:
            in_bin = (y_prob >= bin_lower) & (y_prob <= bin_upper)
        
        prop_in_bin = np.mean(in_bin)
        
        if prop_in_bin > 0:
            avg_confidence = np.mean(y_prob[in_bin])
            avg_accuracy = np.mean(y_true[in_bin])
            ece += np.abs(avg_accuracy - avg_confidence) * prop_in_bin
    
    return float(ece)


def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """
    Calculate Brier Score.
    
    Args:
        y_true: True binary labels.
        y_prob: Predicted probabilities.
    
    Returns:
        Brier Score.
    """
    return float(brier_score_loss(y_true, y_prob))


def pca_shift(
    train_features: np.ndarray, 
    test_features: np.ndarray, 
    n_components: float = 0.95
) -> float:
    """
    Calculate PCA-based covariate shift.
    
    This metric measures the shift in the data distribution by projecting
    both train and test sets onto the PCA components derived from the train set
    and comparing the mean squared distance of the test set from the train mean.
    
    Formula:
    1. Fit PCA on train_features.
    2. Transform both train and test to PCA space.
    3. Compute the mean of train in PCA space.
    4. Compute the mean squared distance of test points from the train mean.
    
    Args:
        train_features: Training feature matrix (n_samples, n_features).
        test_features: Test feature matrix.
        n_components: Number of components or variance ratio to retain.
    
    Returns:
        PCA shift value (float).
    """
    if train_features.shape[0] == 0 or test_features.shape[0] == 0:
        return 0.0
    
    # Ensure 2D
    train_features = np.asarray(train_features)
    test_features = np.asarray(test_features)
    
    # Handle case where features might be 1D (unlikely for this task, but safe)
    if len(train_features.shape) == 1:
        train_features = train_features.reshape(-1, 1)
    if len(test_features.shape) == 1:
        test_features = test_features.reshape(-1, 1)
    
    # Fit PCA on training data
    pca = PCA(n_components=n_components)
    pca.fit(train_features)
    
    # Transform data
    train_pca = pca.transform(train_features)
    test_pca = pca.transform(test_features)
    
    # Calculate mean of training data in PCA space
    train_mean = np.mean(train_pca, axis=0)
    
    # Calculate mean squared distance of test data from training mean
    # This represents how far the test distribution has shifted from the training distribution
    distances = np.linalg.norm(test_pca - train_mean, axis=1)
    shift = np.mean(distances)
    
    return float(shift)


def key_feature_shift(
    train_features: np.ndarray, 
    test_features: np.ndarray, 
    feature_names: Optional[List[str]] = None
) -> float:
    """
    Calculate Key Feature Mean Shift.
    
    This metric computes the mean absolute difference in feature means
    between the training and test sets, normalized by the training standard deviation.
    
    Formula:
    Shift = (1/n_features) * sum( |mean_test_j - mean_train_j| / std_train_j )
    
    Args:
        train_features: Training feature matrix.
        test_features: Test feature matrix.
        feature_names: Optional list of feature names (not used in calculation but for logging).
    
    Returns:
        Key Feature Shift value (float).
    """
    train_features = np.asarray(train_features)
    test_features = np.asarray(test_features)
    
    if train_features.shape[0] == 0 or test_features.shape[0] == 0:
        return 0.0
    
    # Ensure 2D
    if len(train_features.shape) == 1:
        train_features = train_features.reshape(-1, 1)
    if len(test_features.shape) == 1:
        test_features = test_features.reshape(-1, 1)
    
    # Calculate means and stds
    train_mean = np.mean(train_features, axis=0)
    train_std = np.std(train_features, axis=0)
    
    # Avoid division by zero
    train_std = np.where(train_std == 0, 1.0, train_std)
    
    test_mean = np.mean(test_features, axis=0)
    
    # Calculate normalized mean shift
    shifts = np.abs(test_mean - train_mean) / train_std
    
    return float(np.mean(shifts))


def spearman_correlation(
    x: Union[List[float], np.ndarray], 
    y: Union[List[float], np.ndarray]
) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation and p-value.
    
    Args:
        x: First variable.
        y: Second variable.
    
    Returns:
        Tuple of (correlation coefficient, p-value).
    """
    rho, p_value = spearmanr(x, y)
    return float(rho), float(p_value)