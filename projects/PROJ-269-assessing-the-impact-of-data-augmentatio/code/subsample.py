"""
Stratified subsampling module.

This module provides functions for creating stratified subsamples from datasets
while preserving class ratios and handling edge cases.
"""

import os
import logging
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def balance(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """
    Balance a dataframe by oversampling the minority class.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.

    Returns:
        Balanced DataFrame.
    """
    counts = df[target_col].value_counts()
    if len(counts) < 2:
        return df

    minority = counts.idxmin()
    majority = counts.idxmax()

    minority_df = df[df[target_col] == minority]
    majority_df = df[df[target_col] == majority]

    n_minority = len(minority_df)
    n_majority = len(majority_df)

    if n_minority >= n_majority:
        return df

    # Oversample minority
    minority_oversampled = minority_df.sample(n=n_majority, replace=True, random_state=42)

    return pd.concat([majority_df, minority_oversampled], ignore_index=True)


def detect_target_column(df: pd.DataFrame) -> str:
    """
    Detect the target column in a DataFrame.

    Priority: 'target' > 'class' > 'label' > last column.

    Args:
        df: Input DataFrame.

    Returns:
        Name of the target column.
    """
    priority = ['target', 'class', 'label']
    for col in priority:
        if col in df.columns:
            return col
    return df.columns[-1]


def validate_class_counts(df: pd.DataFrame, target_col: str, n: int) -> Tuple[bool, str]:
    """
    Validate that class counts are sufficient for stratified sampling.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        n: Desired sample size.

    Returns:
        Tuple of (is_valid, reason).
    """
    counts = df[target_col].value_counts()
    if len(counts) < 2:
        return False, "Insufficient classes for stratification"

    min_count = counts.min()
    if min_count < 5:
        return False, f"Minimum class count ({min_count}) is less than 5"

    return True, "Valid"


def create_stratified_subsample(
    df: pd.DataFrame,
    n: int,
    target_col: str,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Create a stratified subsample of size n.

    Args:
        df: Input DataFrame.
        n: Desired sample size.
        target_col: Name of the target column.
        random_state: Random seed for reproducibility.

    Returns:
        Stratified subsample DataFrame.
    """
    if len(df) <= n:
        return df.reset_index(drop=True)

    sample = df.groupby(target_col, group_keys=False).apply(
        lambda x: x.sample(n=max(1, int(len(x) * n / len(df))), random_state=random_state)
    )

    # Ensure we don't exceed n
    if len(sample) > n:
        sample = sample.sample(n=n, random_state=random_state)

    return sample.reset_index(drop=True)


def log_skipped_configuration(
    dataset: str,
    size: int,
    reason: str,
    log_path: str
) -> None:
    """
    Log a skipped configuration to a JSON log file.

    Args:
        dataset: Name of the dataset.
        size: Sample size that was skipped.
        reason: Reason for skipping.
        log_path: Path to the JSON log file.
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

    logger.warning(f"Skipped configuration: {dataset}, N={size}, reason: {reason}")


def process_dataset(
    dataset_path: str,
    n: int,
    log_path: str
) -> Optional[pd.DataFrame]:
    """
    Process a dataset: detect target, validate, and create stratified subsample.

    Args:
        dataset_path: Path to the dataset CSV file.
        n: Desired sample size.
        log_path: Path to the skipped configurations log.

    Returns:
        Stratified subsample DataFrame, or None if skipped.
    """
    df = pd.read_csv(dataset_path)
    target_col = detect_target_column(df)

    is_valid, reason = validate_class_counts(df, target_col, n)
    if not is_valid:
        log_skipped_configuration(
            os.path.basename(dataset_path),
            n,
            reason,
            log_path
        )
        return None

    return create_stratified_subsample(df, n, target_col)


def main() -> None:
    """Main entry point for subsampling."""
    # This is a module-level entry point for testing
    logger.info("Subsample module loaded successfully")


if __name__ == "__main__":
    main()
