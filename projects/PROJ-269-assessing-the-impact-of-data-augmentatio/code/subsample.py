"""
Stratified subsampling module for the augmentation impact study.

Provides functions to create stratified subsamples of datasets for
small-sample statistical power analysis. Handles edge cases where
class counts are insufficient for the requested sample size.
"""

import os
import logging
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DERIVED_DATA_DIR: Path = Path("data/derived")
DERIVED_DATA_DIR.mkdir(parents=True, exist_ok=True)

SKIPPED_CONFIGS_LOG: Path = DERIVED_DATA_DIR / "skipped_configurations.log"


def detect_target_column(df: pd.DataFrame) -> str:
    """
    Detect the target column in a DataFrame using priority rules.

    Priority order: 'target' > 'class' > 'label' > last column.

    Args:
        df: Input DataFrame to inspect.

    Returns:
        Name of the target column.
    """
    priority_columns: List[str] = ['target', 'class', 'label']

    for col in priority_columns:
        if col in df.columns:
            logger.debug(f"Found target column '{col}' by priority match")
            return col

    # Default to last column
    target_col: str = df.columns[-1]
    logger.debug(f"No priority column found, using last column '{target_col}'")
    return target_col


def validate_class_counts(df: pd.DataFrame, target_col: str, n: int) -> Tuple[bool, Dict[str, int]]:
    """
    Validate that class distribution allows for stratified subsampling of size n.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        n: Desired sample size.

    Returns:
        Tuple of (is_valid, class_counts_dict).
        is_valid is True if each class has at least 2 samples (minimum for stratification).
    """
    class_counts: pd.Series = df[target_col].value_counts()
    counts_dict: Dict[str, int] = class_counts.to_dict()

    # Need at least 2 samples per class for meaningful stratification
    min_count: int = class_counts.min()

    if min_count < 2:
        logger.warning(
            f"Class distribution too sparse: min count = {min_count}. "
            f"Cannot stratify effectively."
        )
        return False, counts_dict

    # Check if we can get n samples while maintaining proportions
    # Each class should ideally contribute at least 1 sample
    if len(counts_dict) > n:
        logger.warning(
            f"Number of classes ({len(counts_dict)}) exceeds sample size ({n}). "
            f"Cannot sample one from each class."
        )
        return False, counts_dict

    return True, counts_dict


def create_stratified_subsample(
    df: pd.DataFrame,
    target_col: str,
    n: int,
    random_state: int
) -> Optional[pd.DataFrame]:
    """
    Create a stratified subsample of the DataFrame.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        n: Desired sample size.
        random_state: Random seed for reproducibility.

    Returns:
        Stratified subsample DataFrame, or None if subsampling failed.
    """
    try:
        np.random.seed(random_state)

        # Use pandas built-in stratified sampling
        subsample: pd.DataFrame = df.groupby(
            target_col,
            group_keys=False
        ).apply(
            lambda x: x.sample(
                n=max(1, int(len(x) * n / len(df))),
                random_state=random_state
            )
        )

        # Ensure we have exactly n samples (or as close as possible)
        if len(subsample) > n:
            subsample = subsample.sample(n=n, random_state=random_state)

        logger.debug(
            f"Created stratified subsample of size {len(subsample)} "
            f"from {len(df)} original rows"
        )

        return subsample

    except Exception as e:
        logger.error(f"Stratified subsampling failed: {str(e)}")
        return None


def log_skipped_configuration(
    dataset_name: str,
    n: int,
    target_col: str,
    class_counts: Dict[str, int],
    reason: str
) -> None:
    """
    Log a skipped configuration to the derived data log file.

    Args:
        dataset_name: Name of the dataset.
        n: Requested sample size.
        target_col: Target column name.
        class_counts: Dictionary of class counts.
        reason: Reason for skipping.
    """
    log_entry: Dict[str, Any] = {
        "dataset": dataset_name,
        "requested_n": n,
        "target_column": target_col,
        "class_counts": class_counts,
        "reason": reason
    }

    with open(SKIPPED_CONFIGS_LOG, "a") as f:
        f.write(f"{log_entry}\n")

    logger.warning(
        f"Skipped configuration: {dataset_name} (n={n}, reason: {reason})"
    )


def process_dataset(
    df: pd.DataFrame,
    dataset_name: str,
    n: int,
    random_state: int
) -> Optional[pd.DataFrame]:
    """
    Process a single dataset: detect target, validate, and subsample.

    Args:
        df: Input DataFrame.
        dataset_name: Name of the dataset.
        n: Desired sample size.
        random_state: Random seed.

    Returns:
        Processed subsample DataFrame, or None if processing failed.
    """
    target_col: str = detect_target_column(df)
    logger.info(f"Processing {dataset_name}: target column = '{target_col}', size = {n}")

    is_valid, class_counts = validate_class_counts(df, target_col, n)

    if not is_valid:
        # Attempt to reduce N
        reduced_n: int = n
        while reduced_n >= 5:
            reduced_n -= 5
            is_valid, _ = validate_class_counts(df, target_col, reduced_n)
            if is_valid:
                logger.info(
                    f"Reduced sample size from {n} to {reduced_n} for {dataset_name}"
                )
                break

        if not is_valid:
            log_skipped_configuration(
                dataset_name, n, target_col, class_counts,
                "Cannot reduce N further while preserving stratification"
            )
            return None

        n = reduced_n

    subsample: Optional[pd.DataFrame] = create_stratified_subsample(
        df, target_col, n, random_state
    )

    if subsample is None:
        log_skipped_configuration(
            dataset_name, n, target_col, class_counts,
            "Subsampling algorithm failed"
        )
        return None

    return subsample


def main() -> int:
    """
    Main function to run subsampling on all datasets.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    # This would typically be called from main.py with specific configurations
    logger.info("Subsampling module ready. Call process_dataset() with specific configs.")
    return 0


if __name__ == "__main__":
    exit(main())
