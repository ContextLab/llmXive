"""
Data Augmentation Module for Small Sample Statistical Power Study.

Implements Gaussian noise injection, SMOTE, and Random Oversampling using
imbalanced-learn. Ensures CPU-only execution and handles zero-variance samples.
"""

import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Union

from sklearn.utils import check_random_state
from imblearn.over_sampling import SMOTE, RandomOverSampler
from imblearn.utils import check_neighbors_object

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _detect_target_column(df: pd.DataFrame) -> str:
    """
    Detect the target column using the priority: 'target' -> 'class' -> 'label' -> last column.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Name of the target column.
    """
    priority = ['target', 'class', 'label']
    for col in priority:
        if col in df.columns:
            return col
    # Default to last column
    return df.columns[-1]

def _check_zero_variance(X: np.ndarray) -> List[int]:
    """
    Identify columns with zero variance (constant values).
    
    Args:
        X: Feature array (n_samples, n_features).
        
    Returns:
        List of column indices with zero variance.
    """
    if X.shape[0] == 0:
        return list(range(X.shape[1]))
    
    zero_var_cols = []
    for i in range(X.shape[1]):
        if np.var(X[:, i]) == 0:
            zero_var_cols.append(i)
    return zero_var_cols

def inject_gaussian_noise(
    X: np.ndarray,
    y: np.ndarray,
    noise_std: float = 0.1,
    random_state: Optional[Union[int, np.random.RandomState]] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Inject Gaussian noise into the feature matrix.
    
    Args:
        X: Feature array (n_samples, n_features).
        y: Target array (n_samples,).
        noise_std: Standard deviation of the Gaussian noise.
        random_state: Random seed or RandomState instance.
        
    Returns:
        Tuple of (noisy_X, y).
    """
    rng = check_random_state(random_state)
    noise = rng.normal(0, noise_std, size=X.shape)
    noisy_X = X + noise
    return noisy_X, y

def apply_smote(
    X: np.ndarray,
    y: np.ndarray,
    random_state: Optional[Union[int, np.random.RandomState]] = None,
    k_neighbors: int = 5,
    n_jobs: int = 1
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply SMOTE (Synthetic Minority Over-sampling Technique).
    
    Ensures CPU-only execution (n_jobs=1) and handles edge cases where
    minority class samples are insufficient.
    
    Args:
        X: Feature array (n_samples, n_features).
        y: Target array (n_samples,).
        random_state: Random seed or RandomState instance.
        k_neighbors: Number of nearest neighbors to use for synthesis.
        n_jobs: Number of CPU jobs (forced to 1 for CPU-only constraint).
        
    Returns:
        Tuple of (resampled_X, resampled_y).
        
    Raises:
        ValueError: If minority class has fewer than 2 samples or if
                   k_neighbors is larger than minority class size.
    """
    rng = check_random_state(random_state)
    
    # Check for zero variance features before SMOTE
    zero_var_cols = _check_zero_variance(X)
    if len(zero_var_cols) > 0:
        logger.warning(f"Removing {len(zero_var_cols)} zero-variance features before SMOTE: {zero_var_cols}")
        X_clean = np.delete(X, zero_var_cols, axis=1)
    else:
        X_clean = X
    
    # Validate minimum sample counts per class
    unique, counts = np.unique(y, return_counts=True)
    min_count = min(counts)
    if min_count < 2:
        raise ValueError(
            f"SMOTE requires at least 2 samples per class. "
            f"Found minimum class count: {min_count}"
        )
    
    # Adjust k_neighbors if necessary
    effective_k = min(k_neighbors, min_count - 1)
    if effective_k < 1:
        raise ValueError(
            f"Cannot apply SMOTE with k_neighbors={k_neighbors} given "
            f"minimum class size {min_count}. Need at least 2 samples."
        )
    
    try:
        smote = SMOTE(
            k_neighbors=effective_k,
            random_state=rng,
            n_jobs=1  # Force CPU-only
        )
        resampled_X, resampled_y = smote.fit_resample(X_clean, y)
        
        # If we removed zero-variance columns, we need to handle the output shape
        # SMOTE preserves the feature dimensions of the input it received
        return resampled_X, resampled_y
        
    except Exception as e:
        logger.error(f"SMOTE failed: {str(e)}")
        raise

def apply_random_oversampling(
    X: np.ndarray,
    y: np.ndarray,
    random_state: Optional[Union[int, np.random.RandomState]] = None,
    sampling_strategy: str = 'auto'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Random Oversampling to balance the dataset.
    
    Args:
        X: Feature array (n_samples, n_features).
        y: Target array (n_samples,).
        random_state: Random seed or RandomState instance.
        sampling_strategy: Strategy for resampling ('auto', 'not minority', or float).
        
    Returns:
        Tuple of (resampled_X, resampled_y).
    """
    rng = check_random_state(random_state)
    
    # Check for zero variance features
    zero_var_cols = _check_zero_variance(X)
    if len(zero_var_cols) > 0:
        logger.warning(f"Removing {len(zero_var_cols)} zero-variance features before Random Oversampling: {zero_var_cols}")
        X_clean = np.delete(X, zero_var_cols, axis=1)
    else:
        X_clean = X
    
    try:
        ros = RandomOverSampler(
            sampling_strategy=sampling_strategy,
            random_state=rng
        )
        resampled_X, resampled_y = ros.fit_resample(X_clean, y)
        return resampled_X, resampled_y
        
    except Exception as e:
        logger.error(f"Random Oversampling failed: {str(e)}")
        raise

def augment_dataset(
    df: pd.DataFrame,
    method: str,
    noise_std: float = 0.1,
    k_neighbors: int = 5,
    random_state: Optional[Union[int, np.random.RandomState]] = None
) -> Tuple[pd.DataFrame, str]:
    """
    Apply a specified augmentation method to a dataset.
    
    Args:
        df: Input DataFrame.
        method: One of 'gaussian_noise', 'smote', 'random_oversampling'.
        noise_std: Standard deviation for Gaussian noise.
        k_neighbors: Number of neighbors for SMOTE.
        random_state: Random seed.
        
    Returns:
        Tuple of (augmented_df, method_name).
        
    Raises:
        ValueError: If method is unknown or augmentation fails.
    """
    target_col = _detect_target_column(df)
    y = df[target_col].values
    X = df.drop(columns=[target_col]).values
    
    if method == 'gaussian_noise':
        X_aug, y_aug = inject_gaussian_noise(X, y, noise_std=noise_std, random_state=random_state)
        # Reconstruct DataFrame
        feature_cols = [c for c in df.columns if c != target_col]
        aug_df = pd.DataFrame(X_aug, columns=feature_cols)
        aug_df[target_col] = y_aug
        return aug_df, method
        
    elif method == 'smote':
        X_aug, y_aug = apply_smote(X, y, random_state=random_state, k_neighbors=k_neighbors)
        feature_cols = [c for c in df.columns if c != target_col]
        # Ensure we have the right number of feature columns
        if X_aug.shape[1] != len(feature_cols):
            # This can happen if zero-variance columns were removed
            # We'll use the first N columns of the original feature list
            used_features = feature_cols[:X_aug.shape[1]]
            aug_df = pd.DataFrame(X_aug, columns=used_features)
            aug_df[target_col] = y_aug
        else:
            aug_df = pd.DataFrame(X_aug, columns=feature_cols)
            aug_df[target_col] = y_aug
        return aug_df, method
        
    elif method == 'random_oversampling':
        X_aug, y_aug = apply_random_oversampling(X, y, random_state=random_state)
        feature_cols = [c for c in df.columns if c != target_col]
        if X_aug.shape[1] != len(feature_cols):
            used_features = feature_cols[:X_aug.shape[1]]
            aug_df = pd.DataFrame(X_aug, columns=used_features)
            aug_df[target_col] = y_aug
        else:
            aug_df = pd.DataFrame(X_aug, columns=feature_cols)
            aug_df[target_col] = y_aug
        return aug_df, method
        
    else:
        raise ValueError(f"Unknown augmentation method: {method}")

def main():
    """
    Demonstration of augmentation functions with real data.
    This script expects preprocessed data from T005 (subsample.py) to exist.
    """
    # Define paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data' / 'derived'
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return
    
    # Find a sample dataset to demonstrate augmentation
    sample_files = list(data_dir.glob('*.csv'))
    if not sample_files:
        logger.warning("No CSV files found in data/derived/. Skipping demonstration.")
        return
    
    sample_file = sample_files[0]
    logger.info(f"Loading sample dataset: {sample_file}")
    
    df = pd.read_csv(sample_file)
    logger.info(f"Loaded dataset with {len(df)} samples, {len(df.columns)} columns")
    
    # Demonstrate each augmentation method
    methods = ['gaussian_noise', 'smote', 'random_oversampling']
    
    for method in methods:
        try:
            logger.info(f"Applying {method}...")
            aug_df, applied_method = augment_dataset(
                df, 
                method=method, 
                random_state=42
            )
            logger.info(f"  Original shape: {df.shape} -> Augmented shape: {aug_df.shape}")
            logger.info(f"  Target distribution:\n{aug_df['target' if 'target' in aug_df.columns else 'class' if 'class' in aug_df.columns else 'label' if 'label' in aug_df.columns else aug_df.columns[-1]].value_counts()}")
            
            # Save augmented dataset
            output_path = data_dir / f"{sample_file.stem}_{applied_method}.csv"
            aug_df.to_csv(output_path, index=False)
            logger.info(f"  Saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"  Failed to apply {method}: {str(e)}")
            
    logger.info("Augmentation demonstration complete.")

if __name__ == '__main__':
    main()
