"""
Data augmentation module.

This module provides functions for data augmentation techniques including
Gaussian noise injection, SMOTE, and Random Oversampling.
"""

import os
import logging
from typing import Tuple, Optional, List, Dict, Union
from pathlib import Path
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE, RandomOverSampler
from imblearn.utils import check_neighbors_object

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log_skipped_smote_configuration(
    dataset: str,
    size: int,
    reason: str,
    log_path: str
) -> None:
    """
    Log a skipped SMOTE configuration.

    Args:
        dataset: Name of the dataset.
        size: Sample size.
        reason: Reason for skipping.
        log_path: Path to the log file.
    """
    entry = {
        "dataset": dataset,
        "size": size,
        "reason": reason,
        "timestamp": "2024-01-01T00:00:00"
    }

    log_data: List[Dict[str, Any]] = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                log_data = json.load(f)
        except json.JSONDecodeError:
            log_data = []

    log_data.append(entry)

    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)

    logger.warning(f"Skipped SMOTE: {dataset}, N={size}, reason: {reason}")


def detect_zero_variance_columns(df: pd.DataFrame) -> List[str]:
    """
    Detect columns with zero variance.

    Args:
        df: Input DataFrame.

    Returns:
        List of column names with zero variance.
    """
    zero_var_cols = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].var() == 0:
            zero_var_cols.append(col)
    return zero_var_cols


def exclude_zero_variance_samples(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """
    Exclude samples that result in zero variance.

    Args:
        df: Input DataFrame.

    Returns:
        Tuple of (cleaned DataFrame, was_excluded).
    """
    zero_var_cols = detect_zero_variance_columns(df)
    if zero_var_cols:
        logger.warning(f"Excluding zero variance columns: {zero_var_cols}")
        df = df.drop(columns=zero_var_cols)
        return df, True
    return df, False


def inject_gaussian_noise(
    df: pd.DataFrame,
    std: float = 0.01,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Inject Gaussian noise into numeric columns.

    Args:
        df: Input DataFrame.
        std: Standard deviation of the noise.
        random_state: Random seed.

    Returns:
        DataFrame with injected noise.
    """
    df_copy = df.copy()
    numeric_cols = df_copy.select_dtypes(include=[np.number]).columns

    np.random.seed(random_state)
    for col in numeric_cols:
        noise = np.random.normal(0, std, size=len(df_copy))
        df_copy[col] = df_copy[col] + noise

    return df_copy


def apply_smote(
    df: pd.DataFrame,
    target_col: str,
    random_state: int = 42,
    log_path: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Apply SMOTE augmentation.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        random_state: Random seed.
        log_path: Path to log file for skipped configurations.

    Returns:
        Augmented DataFrame, or None if skipped.
    """
    if len(df) < 5:
        if log_path:
            log_skipped_smote_configuration(
                "unknown",
                len(df),
                "N < 5",
                log_path
            )
        return None

    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Check for extreme imbalance
    counts = y.value_counts()
    if len(counts) < 2:
        return df

    min_count = counts.min()
    if min_count < 5:
        if log_path:
            log_skipped_smote_configuration(
                "unknown",
                len(df),
                "Extreme imbalance (min class < 5)",
                log_path
            )
        return None

    try:
        smote = SMOTE(random_state=random_state, k_neighbors=min(5, min_count - 1))
        X_res, y_res = smote.fit_resample(X, y)

        result = pd.DataFrame(X_res, columns=X.columns)
        result[target_col] = y_res

        # Check for zero variance
        result, _ = exclude_zero_variance_samples(result)

        return result

    except Exception as e:
        logger.error(f"SMOTE failed: {str(e)}")
        if log_path:
            log_skipped_smote_configuration(
                "unknown",
                len(df),
                f"SMOTE error: {str(e)}",
                log_path
            )
        return None


def apply_random_oversampling(
    df: pd.DataFrame,
    target_col: str,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Apply random oversampling.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        random_state: Random seed.

    Returns:
        Oversampled DataFrame.
    """
    X = df.drop(columns=[target_col])
    y = df[target_col]

    ros = RandomOverSampler(random_state=random_state)
    X_res, y_res = ros.fit_resample(X, y)

    result = pd.DataFrame(X_res, columns=X.columns)
    result[target_col] = y_res

    return result


def augment_dataset(
    df: pd.DataFrame,
    method: str,
    target_col: str,
    std: float = 0.01,
    random_state: int = 42,
    log_path: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Augment a dataset using the specified method.

    Args:
        df: Input DataFrame.
        method: Augmentation method ('gaussian', 'smote', 'random_oversample').
        target_col: Name of the target column.
        std: Standard deviation for Gaussian noise.
        random_state: Random seed.
        log_path: Path to log file for skipped configurations.

    Returns:
        Augmented DataFrame, or None if skipped.
    """
    if method == 'gaussian':
        return inject_gaussian_noise(df, std=std, random_state=random_state)
    elif method == 'smote':
        return apply_smote(df, target_col, random_state=random_state, log_path=log_path)
    elif method == 'random_oversample':
        return apply_random_oversampling(df, target_col, random_state=random_state)
    else:
        raise ValueError(f"Unknown augmentation method: {method}")


def main() -> None:
    """Main entry point for augmentation."""
    logger.info("Augment module loaded successfully")


if __name__ == "__main__":
    main()
