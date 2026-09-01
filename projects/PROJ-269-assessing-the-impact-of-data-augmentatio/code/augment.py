"""
Data augmentation module for statistical power analysis.

This module implements Gaussian noise injection, SMOTE, and Random
Oversampling techniques using `imbalanced-learn`. It includes edge
case handling for zero-variance samples and extreme imbalance.
"""

import os
import logging
from typing import Tuple, Optional, List, Dict, Union
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_skipped_smote_configuration(
    dataset: str,
    size: int,
    reason: str,
    log_path: Path,
    timestamp: Optional[str] = None
) -> None:
    """
    Log a skipped SMOTE configuration to a JSON log file.

    Args:
        dataset (str): The name of the dataset.
        size (int): The sample size.
        reason (str): The reason for skipping.
        log_path (Path): The path to the log file.
        timestamp (Optional[str]): ISO format timestamp.
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    record = {
        "dataset": dataset,
        "size": size,
        "reason": reason,
        "timestamp": timestamp
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    if log_path.exists():
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    records = json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"Existing log file {log_path} is not valid JSON. Overwriting.")
            records = []

    records.append(record)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

def detect_zero_variance_columns(df: pd.DataFrame) -> List[str]:
    """
    Detect columns with zero variance (constant values).

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        List[str]: List of column names with zero variance.
    """
    zero_var_cols = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].nunique() == 1:
            zero_var_cols.append(col)
    return zero_var_cols

def exclude_zero_variance_samples(
    X: np.ndarray,
    y: np.ndarray,
    threshold: float = 1e-5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Exclude samples that result in zero variance columns after augmentation.

    Args:
        X (np.ndarray): Feature matrix.
        y (np.ndarray): Target vector.
        threshold (float): Variance threshold.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Filtered feature matrix and target vector.
    """
    if X.shape[0] == 0:
        return X, y

    variances = np.var(X, axis=0)
    valid_cols = variances > threshold

    if not np.any(valid_cols):
        return np.array([]), np.array([])

    return X[:, valid_cols], y

def inject_gaussian_noise(
    X: np.ndarray,
    std: float = 0.01,
    random_state: Optional[int] = None
) -> np.ndarray:
    """
    Inject Gaussian noise into the feature matrix.

    Args:
        X (np.ndarray): Feature matrix.
        std (float): Standard deviation of the noise.
        random_state (Optional[int]): Random seed.

    Returns:
        np.ndarray: Noisy feature matrix.
    """
    rng = np.random.default_rng(random_state)
    noise = rng.normal(0, std, X.shape)
    return X + noise

def apply_smote(
    X: np.ndarray,
    y: np.ndarray,
    k_neighbors: int = 5,
    random_state: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply SMOTE augmentation to the dataset.

    Args:
        X (np.ndarray): Feature matrix.
        y (np.ndarray): Target vector.
        k_neighbors (int): Number of nearest neighbors.
        random_state (Optional[int]): Random seed.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Augmented feature matrix and target vector.
    """
    try:
        from imblearn.over_sampling import SMOTE
    except ImportError:
        raise ImportError("imbalanced-learn is required for SMOTE.")

    smote = SMOTE(k_neighbors=k_neighbors, random_state=random_state)
    return smote.fit_resample(X, y)

def apply_random_oversampling(
    X: np.ndarray,
    y: np.ndarray,
    random_state: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Random Oversampling to the dataset.

    Args:
        X (np.ndarray): Feature matrix.
        y (np.ndarray): Target vector.
        random_state (Optional[int]): Random seed.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Augmented feature matrix and target vector.
    """
    try:
        from imblearn.over_sampling import RandomOverSampler
    except ImportError:
        raise ImportError("imbalanced-learn is required for Random Oversampling.")

    ros = RandomOverSampler(random_state=random_state)
    return ros.fit_resample(X, y)

def augment_dataset(
    df: pd.DataFrame,
    target_col: str,
    method: str,
    **kwargs
) -> pd.DataFrame:
    """
    Augment a dataset using the specified method.

    Args:
        df (pd.DataFrame): The input DataFrame.
        target_col (str): The name of the target column.
        method (str): The augmentation method ('gaussian', 'smote', 'random_oversample').
        **kwargs: Additional arguments for the augmentation function.

    Returns:
        pd.DataFrame: The augmented DataFrame.
    """
    X = df.drop(columns=[target_col]).values
    y = df[target_col].values

    if method == 'gaussian':
        std = kwargs.get('std', 0.01)
        X_aug = inject_gaussian_noise(X, std=std, random_state=kwargs.get('random_state'))
        # No change in y for noise injection
        return pd.DataFrame(X_aug, columns=df.drop(columns=[target_col]).columns)
    elif method == 'smote':
        X_aug, y_aug = apply_smote(X, y, **kwargs)
    elif method == 'random_oversample':
        X_aug, y_aug = apply_random_oversampling(X, y, **kwargs)
    else:
        raise ValueError(f"Unknown augmentation method: {method}")

    # Reconstruct DataFrame
    aug_df = pd.DataFrame(X_aug, columns=df.drop(columns=[target_col]).columns)
    aug_df[target_col] = y_aug
    return aug_df

def main() -> None:
    """
    Main entry point for the augmentation script.

    Note: This script is typically called by the simulation pipeline.
    """
    logger.info("Augmentation module ready.")

if __name__ == "__main__":
    main()
