"""
Metrics module for quantifying calibration drift and covariate shift.

Implements:
- PCA Shift: Projects features onto principal components and measures the
  mean shift of the projection magnitude between train and test sets.
- Key Feature Shift: Measures the mean absolute difference of specific
  feature means between train and test sets.

Note: Wasserstein distance is explicitly NOT implemented per project plan
(Plan Complexity Tracking) as it is statistically invalid for high-dimensional
raw feature vectors without dimensionality reduction.
"""
import numpy as np
from sklearn.decomposition import PCA
from typing import List, Optional, Tuple, Union

# Type aliases for clarity
FeatureArray = np.ndarray
FloatArray = np.ndarray


def pca_shift(
    train_features: FeatureArray,
    test_features: FeatureArray,
    n_components: Union[int, float] = 0.95
) -> float:
    """
    Calculate PCA-based covariate shift between train and test feature sets.
    
    This metric projects both datasets onto the principal components derived
    from the training data, then calculates the Euclidean distance between
    the mean projection vectors.
    
    Formula Reference:
    1. Fit PCA on train_features to obtain components (W).
    2. Project train: Z_train = (train - mean_train) @ W
    3. Project test:  Z_test  = (test  - mean_train) @ W  (using train mean for consistency)
    4. Shift = || mean(Z_train) - mean(Z_test) ||_2
    
    Args:
        train_features: 2D array of shape (n_samples_train, n_features)
        test_features: 2D array of shape (n_samples_test, n_features)
        n_components: Number of components or variance ratio to retain (default 0.95).
    
    Returns:
        float: The Euclidean distance (L2 norm) between the mean projections.
    
    Raises:
        ValueError: If input dimensions mismatch or n_components is invalid.
    """
    if train_features.shape[1] != test_features.shape[1]:
        raise ValueError(
            f"Feature dimensions mismatch: train has {train_features.shape[1]}, "
            f"test has {test_features.shape[1]}"
        )
    
    if train_features.shape[0] == 0 or test_features.shape[0] == 0:
        raise ValueError("Input arrays cannot be empty.")
    
    # Ensure float64 for numerical stability
    X_train = np.asarray(train_features, dtype=np.float64)
    X_test = np.asarray(test_features, dtype=np.float64)
    
    # Fit PCA on training data
    pca = PCA(n_components=n_components)
    # We fit only on train to establish the reference space
    pca.fit(X_train)
    
    # Transform both sets using the train-derived components
    # Note: We use the same centering (mean of train) for both to measure shift relative to the model's view
    # However, standard practice for shift detection often centers both by their own means to see distributional drift
    # in the component space. The Plan specifies "projection", implying the geometric distance in the subspace.
    # Standard Covariate Shift via PCA usually compares the means in the reduced space.
    # Let's center both by the training mean to see how the test distribution has moved relative to the training origin.
    
    # Center test data using training mean (to detect shift in the learned space)
    X_test_centered = X_test - X_train.mean(axis=0)
    X_train_centered = X_train - X_train.mean(axis=0)
    
    Z_train = pca.transform(X_train_centered)
    Z_test = pca.transform(X_test_centered)
    
    # Calculate mean of projections
    mean_train_proj = np.mean(Z_train, axis=0)
    mean_test_proj = np.mean(Z_test, axis=0)
    
    # Euclidean distance between means
    shift = np.linalg.norm(mean_train_proj - mean_test_proj)
    
    return float(shift)


def key_feature_shift(
    train_features: FeatureArray,
    test_features: FeatureArray,
    feature_names: List[str]
) -> float:
    """
    Calculate Key Feature Mean Shift.
    
    Measures the mean absolute difference in feature means between train and test
    sets for a specified list of features.
    
    Formula Reference:
    Shift = (1 / |K|) * sum(|mean(train_k) - mean(test_k)|) for k in Key Features
    
    Args:
        train_features: 2D array of shape (n_samples_train, n_features)
        test_features: 2D array of shape (n_samples_test, n_features)
        feature_names: List of feature names corresponding to the columns in the arrays.
                       The order must match the column order in the arrays.
    
    Returns:
        float: The average absolute difference in means across the specified features.
    
    Raises:
        ValueError: If feature_names length does not match number of columns.
        IndexError: If feature_names contains names not found (if mapping is used), 
                    but here we assume positional matching.
    """
    if train_features.shape[1] != test_features.shape[1]:
        raise ValueError(
            f"Feature dimensions mismatch: train has {train_features.shape[1]}, "
            f"test has {test_features.shape[1]}"
        )
    
    if len(feature_names) != train_features.shape[1]:
        raise ValueError(
            f"Length of feature_names ({len(feature_names)}) must match "
            f"number of columns ({train_features.shape[1]})"
        )
    
    if train_features.shape[0] == 0 or test_features.shape[0] == 0:
        raise ValueError("Input arrays cannot be empty.")
    
    X_train = np.asarray(train_features, dtype=np.float64)
    X_test = np.asarray(test_features, dtype=np.float64)
    
    # Calculate means for all features
    mean_train = X_train.mean(axis=0)
    mean_test = X_test.mean(axis=0)
    
    # Calculate absolute differences for all features (since feature_names implies we care about the set)
    # If feature_names was a subset, we would index. Here we assume the list covers the columns of interest
    # or the whole set if the list matches the column count.
    # The task says "feature_names=...", implying we might pass a subset.
    # However, the signature implies we are given the names to identify columns.
    # Since we don't have a dict mapping name->index here, we assume the input arrays are already 
    # ordered such that feature_names[i] corresponds to column i.
    # If the user wants a subset, they should pass only those columns in the arrays.
    # To be safe and strictly follow "Key Feature", we calculate the mean over the provided list.
    # Since we can't map names to indices without a schema here, we assume the input arrays 
    # correspond 1:1 with the provided feature_names list in order.
    
    abs_diff = np.abs(mean_train - mean_test)
    
    # If the user passed a subset of names, they should have sliced the arrays.
    # If they passed all names, we average over all.
    # We return the average absolute shift.
    shift = np.mean(abs_diff)
    
    return float(shift)