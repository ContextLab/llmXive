import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Union

from imblearn.over_sampling import SMOTE, RandomOverSampler
from imblearn.utils import check_random_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_zero_variance_columns(df: pd.DataFrame, exclude_target: bool = True, target_col: Optional[str] = None) -> List[str]:
    """
    Detect columns with zero variance (constant values) in the DataFrame.
    
    Args:
        df: Input DataFrame.
        exclude_target: If True, exclude the target column from the check.
        target_col: Name of the target column if exclude_target is True.
        
    Returns:
        List of column names with zero variance.
    """
    if exclude_target and target_col:
        features = df.drop(columns=[target_col])
    else:
        features = df.copy()
        
    # Only check numeric columns for variance
    numeric_features = features.select_dtypes(include=[np.number])
    
    zero_var_cols = []
    for col in numeric_features.columns:
        if numeric_features[col].std() == 0:
            zero_var_cols.append(col)
            
    return zero_var_cols

def inject_gaussian_noise(
    df: pd.DataFrame, 
    std: float = 0.1, 
    target_col: Optional[str] = None,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Inject Gaussian noise into the feature columns of the DataFrame.
    
    Args:
        df: Input DataFrame.
        std: Standard deviation of the Gaussian noise.
        target_col: Name of the target column to exclude from noise injection.
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame with injected noise.
    """
    rng = check_random_state(seed)
    df_noisy = df.copy()
    
    if target_col:
        features = df_noisy.drop(columns=[target_col])
    else:
        features = df_noisy
        
    numeric_features = features.select_dtypes(include=[np.number])
    noise = rng.normal(0, std, size=numeric_features.shape)
    df_noisy[numeric_features.columns] = numeric_features.values + noise
    
    return df_noisy

def apply_smote(
    df: pd.DataFrame, 
    target_col: str, 
    random_state: Optional[int] = None,
    k_neighbors: int = 5
) -> pd.DataFrame:
    """
    Apply SMOTE augmentation to the DataFrame.
    
    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        random_state: Random state for reproducibility.
        k_neighbors: Number of nearest neighbors for SMOTE.
        
    Returns:
        DataFrame with SMOTE-applied samples.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")
        
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Handle zero-variance columns before SMOTE
    zero_var_cols = detect_zero_variance_columns(df, exclude_target=True, target_col=target_col)
    if zero_var_cols:
        logger.warning(f"Removing zero-variance columns before SMOTE: {zero_var_cols}")
        X = X.drop(columns=zero_var_cols)
        
    if X.shape[1] == 0:
        raise ValueError("No features remain after removing zero-variance columns.")
        
    smote = SMOTE(random_state=random_state, k_neighbors=k_neighbors)
    X_resampled, y_resampled = smote.fit_resample(X, y)
    
    df_resampled = pd.DataFrame(X_resampled, columns=X.columns)
    df_resampled[target_col] = y_resampled
    
    return df_resampled

def apply_random_oversampling(
    df: pd.DataFrame, 
    target_col: str, 
    random_state: Optional[int] = None
) -> pd.DataFrame:
    """
    Apply Random Oversampling to the DataFrame.
    
    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        random_state: Random state for reproducibility.
        
    Returns:
        DataFrame with Random Oversampling applied.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")
        
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Handle zero-variance columns before oversampling
    zero_var_cols = detect_zero_variance_columns(df, exclude_target=True, target_col=target_col)
    if zero_var_cols:
        logger.warning(f"Removing zero-variance columns before Random Oversampling: {zero_var_cols}")
        X = X.drop(columns=zero_var_cols)
        
    if X.shape[1] == 0:
        raise ValueError("No features remain after removing zero-variance columns.")
        
    ros = RandomOverSampler(random_state=random_state)
    X_resampled, y_resampled = ros.fit_resample(X, y)
    
    df_resampled = pd.DataFrame(X_resampled, columns=X.columns)
    df_resampled[target_col] = y_resampled
    
    return df_resampled

def augment_dataset(
    df: pd.DataFrame, 
    method: str, 
    target_col: str, 
    noise_std: float = 0.1,
    k_neighbors: int = 5,
    random_state: Optional[int] = None
) -> pd.DataFrame:
    """
    Apply a specified augmentation method to the dataset.
    
    Args:
        df: Input DataFrame.
        method: Augmentation method ('gaussian_noise', 'smote', 'random_oversampling').
        target_col: Name of the target column.
        noise_std: Standard deviation for Gaussian noise.
        k_neighbors: Number of neighbors for SMOTE.
        random_state: Random state for reproducibility.
        
    Returns:
        Augmented DataFrame.
    """
    if method == 'gaussian_noise':
        return inject_gaussian_noise(df, std=noise_std, target_col=target_col, seed=random_state)
    elif method == 'smote':
        return apply_smote(df, target_col=target_col, random_state=random_state, k_neighbors=k_neighbors)
    elif method == 'random_oversampling':
        return apply_random_oversampling(df, target_col=target_col, random_state=random_state)
    else:
        raise ValueError(f"Unknown augmentation method: {method}")

def main():
    """
    Main function for testing augmentation functions.
    """
    # Example usage
    data = {
        'feature1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'feature2': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        'target': [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    }
    df = pd.DataFrame(data)
    
    logger.info("Original DataFrame:")
    logger.info(df)
    
    # Test Gaussian Noise
    df_noisy = augment_dataset(df, 'gaussian_noise', 'target', random_state=42)
    logger.info("\nGaussian Noise Augmented DataFrame:")
    logger.info(df_noisy)
    
    # Test SMOTE
    df_smote = augment_dataset(df, 'smote', 'target', random_state=42)
    logger.info("\nSMOTE Augmented DataFrame:")
    logger.info(df_smote)
    
    # Test Random Oversampling
    df_ros = augment_dataset(df, 'random_oversampling', 'target', random_state=42)
    logger.info("\nRandom Oversampling Augmented DataFrame:")
    logger.info(df_ros)

if __name__ == "__main__":
    main()