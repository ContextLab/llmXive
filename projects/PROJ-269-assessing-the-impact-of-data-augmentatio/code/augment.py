import os
import logging
from typing import Tuple, Optional, List, Dict, Union
from pathlib import Path
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE, RandomOverSampler
from imblearn.utils import check_X_y

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path for skipped configurations log
SKIPPED_CONFIG_LOG_PATH = Path("data/derived/skipped_configurations.log")

def _ensure_log_directory():
    """Ensure the log directory exists."""
    SKIPPED_CONFIG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def log_skipped_smote_configuration(dataset_name: str, sample_size: int, 
                                    class_distribution: Dict[int, int], 
                                    reason: str):
    """
    Logs a skipped SMOTE configuration to a structured JSON log file.
    
    Args:
        dataset_name: Name of the dataset being processed.
        sample_size: Total sample size attempted.
        class_distribution: Dictionary mapping class labels to their counts.
        reason: Specific reason for skipping (e.g., N < 5, extreme imbalance).
    """
    _ensure_log_directory()
    
    log_entry = {
        "dataset": dataset_name,
        "sample_size": sample_size,
        "class_distribution": class_distribution,
        "reason": reason,
        "method": "SMOTE",
        "status": "SKIPPED"
    }
    
    with open(SKIPPED_CONFIG_LOG_PATH, 'a') as f:
        f.write(f"{log_entry}\n")
    
    logger.warning(
        f"SMOTE skipped for {dataset_name} (N={sample_size}): {reason}. "
        f"Class dist: {class_distribution}"
    )

def detect_zero_variance_columns(X: np.ndarray) -> List[int]:
    """
    Detects columns with zero variance (constant values).
    
    Args:
        X: Feature matrix (n_samples, n_features).
        
    Returns:
        List of column indices with zero variance.
    """
    if X.shape[0] < 2:
        return list(range(X.shape[1])) if X.shape[1] > 0 else []
    
    zero_var_indices = []
    for i in range(X.shape[1]):
        if np.std(X[:, i]) == 0:
            zero_var_indices.append(i)
    return zero_var_indices

def exclude_zero_variance_samples(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Removes columns with zero variance from the feature matrix.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        
    Returns:
        Tuple of (X_cleaned, y) with zero-variance columns removed.
    """
    zero_var_cols = detect_zero_variance_columns(X)
    if not zero_var_cols:
        return X, y
    
    keep_cols = [i for i in range(X.shape[1]) if i not in zero_var_cols]
    if not keep_cols:
        # If all columns are zero variance, return empty X
        logger.warning("All columns have zero variance. Returning empty feature matrix.")
        return np.empty((X.shape[0], 0)), y
        
    return X[:, keep_cols], y

def inject_gaussian_noise(X: np.ndarray, std: float = 0.01, seed: Optional[int] = None) -> np.ndarray:
    """
    Injects Gaussian noise into the feature matrix.
    
    Args:
        X: Feature matrix.
        std: Standard deviation of the noise.
        seed: Random seed for reproducibility.
        
    Returns:
        Noisy feature matrix.
    """
    if seed is not None:
        np.random.seed(seed)
    
    noise = np.random.normal(0, std, X.shape)
    return X + noise

def apply_smote(X: np.ndarray, y: np.ndarray, 
                dataset_name: str = "unknown", 
                min_samples: int = 5,
                random_state: Optional[int] = None) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], bool]:
    """
    Applies SMOTE augmentation with robust edge-case handling and logging.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        dataset_name: Name of the dataset for logging purposes.
        min_samples: Minimum required samples to attempt SMOTE.
        random_state: Random state for reproducibility.
        
    Returns:
        Tuple of (X_augmented, y_augmented, success_flag).
        If success_flag is False, X_augmented and y_augmented will be None.
    """
    # Edge Case 1: Check minimum sample size
    if X.shape[0] < min_samples:
        class_counts = pd.Series(y).value_counts().to_dict()
        log_skipped_smote_configuration(
            dataset_name=dataset_name,
            sample_size=X.shape[0],
            class_distribution=class_counts,
            reason=f"Sample size {X.shape[0]} is below minimum threshold {min_samples}"
        )
        return None, None, False

    # Check class distribution for extreme imbalance
    unique, counts = np.unique(y, return_counts=True)
    class_counts = dict(zip(unique, counts))
    
    # Edge Case 2: If any class has < 1 sample after accounting for SMOTE requirements
    # SMOTE typically requires at least one minority sample to generate new ones.
    # If the minority class count is 0 or 1, SMOTE might fail or produce degenerate results.
    min_class_count = min(counts)
    if min_class_count < 1:
        log_skipped_smote_configuration(
            dataset_name=dataset_name,
            sample_size=X.shape[0],
            class_distribution=class_counts,
            reason="Extreme imbalance: one or more classes have insufficient samples (< 1)"
        )
        return None, None, False

    # Edge Case 3: Check if all samples belong to one class (no minority class)
    if len(unique) == 1:
        log_skipped_smote_configuration(
            dataset_name=dataset_name,
            sample_size=X.shape[0],
            class_distribution=class_counts,
            reason="Single class detected; SMOTE cannot be applied"
        )
        return None, None, False

    # Remove zero variance columns before SMOTE
    X_clean, y_clean = exclude_zero_variance_samples(X, y)
    
    if X_clean.shape[1] == 0:
        log_skipped_smote_configuration(
            dataset_name=dataset_name,
            sample_size=X_clean.shape[0],
            class_distribution=class_counts,
            reason="All features had zero variance; SMOTE cannot be applied"
        )
        return None, None, False

    try:
        smote = SMOTE(random_state=random_state, k_neighbors=min(5, min_class_count - 1) if min_class_count > 1 else 1)
        # k_neighbors must be less than the number of samples in the minority class
        X_resampled, y_resampled = smote.fit_resample(X_clean, y_clean)
        return X_resampled, y_resampled, True
    except Exception as e:
        # Catch specific SMOTE errors (e.g., k_neighbors too large)
        log_skipped_smote_configuration(
            dataset_name=dataset_name,
            sample_size=X.shape[0],
            class_distribution=class_counts,
            reason=f"SMOTE execution failed: {str(e)}"
        )
        return None, None, False

def apply_random_oversampling(X: np.ndarray, y: np.ndarray, 
                              dataset_name: str = "unknown",
                              random_state: Optional[int] = None) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], bool]:
    """
    Applies Random Oversampling with edge-case handling.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        dataset_name: Name of the dataset for logging.
        random_state: Random state for reproducibility.
        
    Returns:
        Tuple of (X_oversampled, y_oversampled, success_flag).
    """
    if X.shape[0] < 1:
        logger.warning(f"Random Oversampling skipped for {dataset_name}: Empty dataset.")
        return None, None, False

    unique, counts = np.unique(y, return_counts=True)
    class_counts = dict(zip(unique, counts))

    # Check for single class
    if len(unique) == 1:
        # If single class, random oversampling just duplicates existing data
        # This is valid, but we might want to log it as a special case
        logger.info(f"Random Oversampling on single-class dataset {dataset_name}.")
        ros = RandomOverSampler(random_state=random_state)
        X_res, y_res = ros.fit_resample(X, y)
        return X_res, y_res, True

    try:
        ros = RandomOverSampler(random_state=random_state)
        X_res, y_res = ros.fit_resample(X, y)
        
        # Post-check: ensure no zero variance introduced (unlikely with ROS but good practice)
        if X_res.shape[1] > 0:
            zero_var = detect_zero_variance_columns(X_res)
            if zero_var:
                # Filter out zero variance columns if any
                keep_cols = [i for i in range(X_res.shape[1]) if i not in zero_var]
                if keep_cols:
                    X_res = X_res[:, keep_cols]
                else:
                    logger.warning(f"Random Oversampling resulted in all zero-variance features for {dataset_name}")
                    return None, None, False
        
        return X_res, y_res, True
    except Exception as e:
        logger.error(f"Random Oversampling failed for {dataset_name}: {str(e)}")
        return None, None, False

def augment_dataset(X: np.ndarray, y: np.ndarray, method: str, 
                    dataset_name: str = "unknown", 
                    random_state: Optional[int] = None,
                    **kwargs) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], bool]:
    """
    Generic wrapper for augmentation methods.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        method: One of 'smote', 'random_oversampling', 'gaussian_noise'.
        dataset_name: Name of dataset for logging.
        random_state: Random state.
        **kwargs: Additional arguments passed to specific methods.
        
    Returns:
        Tuple of (X_aug, y_aug, success).
    """
    if method == 'smote':
        return apply_smote(X, y, dataset_name=dataset_name, random_state=random_state)
    elif method == 'random_oversampling':
        return apply_random_oversampling(X, y, dataset_name=dataset_name, random_state=random_state)
    elif method == 'gaussian_noise':
        std = kwargs.get('std', 0.01)
        X_noisy = inject_gaussian_noise(X, std=std, seed=random_state)
        return X_noisy, y, True
    else:
        raise ValueError(f"Unknown augmentation method: {method}")

def main():
    """
    Main entry point for testing augmentation functions.
    """
    # Example usage
    X_test = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]])
    y_test = np.array([0, 0, 1, 1, 1])
    
    print("Testing SMOTE...")
    X_smote, y_smote, success = apply_smote(X_test, y_test, dataset_name="test_smote")
    if success:
        print(f"SMOTE Success: {X_smote.shape}, {y_smote.shape}")
    else:
        print("SMOTE Failed")
        
    print("\nTesting Random Oversampling...")
    X_ros, y_ros, success = apply_random_oversampling(X_test, y_test, dataset_name="test_ros")
    if success:
        print(f"ROS Success: {X_ros.shape}, {y_ros.shape}")
    else:
        print("ROS Failed")

if __name__ == "__main__":
    main()