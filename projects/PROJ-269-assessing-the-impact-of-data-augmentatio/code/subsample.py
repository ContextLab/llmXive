"""
Stratified subsampling module for small-sample statistical power analysis.

This module provides functions to create stratified subsamples of datasets
for N=15, 25, and 40, handling edge cases where class counts are insufficient.
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from sklearn.model_selection import train_test_split

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SAMPLE_SIZES = [15, 25, 40]
DATA_DERIVED_DIR = Path("data/derived")
SKIPPED_LOG_FILE = DATA_DERIVED_DIR / "skipped_configurations.log"

def detect_target_column(df: pd.DataFrame) -> str:
    """
    Detect the target column based on priority: 'target' -> 'class' -> 'label' -> last column.

    Args:
        df: Input DataFrame

    Returns:
        Name of the target column
    """
    priority_names = ['target', 'class', 'label']
    columns = df.columns.tolist()

    for name in priority_names:
        if name in columns:
            logger.info(f"Detected target column '{name}' via priority match.")
            return name

    # Default to last column
    target_col = columns[-1]
    logger.info(f"No priority target found. Defaulting to last column '{target_col}'.")
    return target_col

def validate_class_counts(df: pd.DataFrame, target_col: str, n: int) -> Tuple[bool, str]:
    """
    Validate that each class has at least 5 samples for the requested subsample size.

    Args:
        df: Input DataFrame
        target_col: Name of the target column
        n: Requested subsample size

    Returns:
        Tuple of (is_valid, message)
    """
    class_counts = df[target_col].value_counts()
    min_count = class_counts.min()

    if min_count < 5:
        return False, f"Minimum class count ({min_count}) < 5 for N={n}. Skipping."

    return True, "Valid"

def create_stratified_subsample(
    df: pd.DataFrame,
    target_col: str,
    n: int,
    random_state: int = 42
) -> Optional[pd.DataFrame]:
    """
    Create a stratified subsample of size n.

    Args:
        df: Input DataFrame
        target_col: Name of the target column
        n: Desired subsample size
        random_state: Random seed for reproducibility

    Returns:
        Subsampled DataFrame or None if validation fails
    """
    # Validate class counts first
    is_valid, msg = validate_class_counts(df, target_col, n)
    if not is_valid:
        return None

    # Calculate class proportions
    class_counts = df[target_col].value_counts(normalize=True)
    n_per_class = (class_counts * n).round().astype(int)

    # Ensure total is exactly n (adjust for rounding errors)
    total = n_per_class.sum()
    if total != n:
        diff = n - total
        # Add/subtract from the largest class to minimize impact
        largest_class = n_per_class.idxmax()
        n_per_class[largest_class] += diff

    # Stratified sampling
    try:
        # Use train_test_split with stratify to get exact proportions
        # We split off 'n' samples from the full dataset
        _, subsample = train_test_split(
            df,
            train_size=n,
            stratify=df[target_col],
            random_state=random_state
        )
        return subsample.reset_index(drop=True)
    except Exception as e:
        logger.error(f"Stratified sampling failed: {e}")
        return None

def log_skipped_configuration(
    dataset_name: str,
    n: int,
    reason: str,
    class_counts: Dict[str, int]
) -> None:
    """
    Log skipped configuration details to the skipped_configurations.log file.

    Args:
        dataset_name: Name of the dataset
        n: Requested subsample size
        reason: Reason for skipping
        class_counts: Dictionary of class counts
    """
    DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    log_entry = (
        f"Dataset: {dataset_name} | N: {n} | Reason: {reason} | "
        f"Class Counts: {class_counts}\n"
    )

    with open(SKIPPED_LOG_FILE, 'a') as f:
        f.write(log_entry)

    logger.warning(f"Skipped configuration logged: {log_entry.strip()}")

def process_dataset(
    df: pd.DataFrame,
    dataset_name: str,
    target_col: Optional[str] = None,
    random_state: int = 42
) -> Dict[int, pd.DataFrame]:
    """
    Process a dataset to create stratified subsamples for all sample sizes.

    Args:
        df: Input DataFrame
        dataset_name: Name of the dataset (for logging)
        target_col: Optional target column name (auto-detected if None)
        random_state: Random seed for reproducibility

    Returns:
        Dictionary mapping sample size to subsampled DataFrame
    """
    if target_col is None:
        target_col = detect_target_column(df)

    results = {}

    for n in SAMPLE_SIZES:
        # Check class counts
        class_counts = df[target_col].value_counts()
        min_count = class_counts.min()

        if min_count < 5:
            log_skipped_configuration(
                dataset_name, n,
                f"Min class count ({min_count}) < 5",
                class_counts.to_dict()
            )
            continue

        subsample = create_stratified_subsample(
            df, target_col, n, random_state
        )

        if subsample is not None:
            results[n] = subsample
            logger.info(f"Created stratified subsample N={n} for {dataset_name}")
        else:
            log_skipped_configuration(
                dataset_name, n,
                "Sampling failed (unknown reason)",
                class_counts.to_dict()
            )

    return results

def main():
    """
    Main function to demonstrate subsampling on downloaded datasets.
    Expects datasets in data/raw/ directory.
    """
    data_raw_dir = Path("data/raw")
    if not data_raw_dir.exists():
        logger.error(f"Data directory {data_raw_dir} does not exist.")
        return

    # Clear previous log file
    if SKIPPED_LOG_FILE.exists():
        SKIPPED_LOG_FILE.unlink()

    # Process each dataset
    for csv_file in data_raw_dir.glob("*.csv"):
        dataset_name = csv_file.stem
        logger.info(f"Processing dataset: {dataset_name}")

        try:
            df = pd.read_csv(csv_file)
            logger.info(f"Loaded {dataset_name}: {len(df)} rows, {len(df.columns)} columns")

            # Process subsamples
            results = process_dataset(df, dataset_name)

            # Save results
            for n, subsample in results.items():
                output_path = DATA_DERIVED_DIR / f"{dataset_name}_n{n}.csv"
                subsample.to_csv(output_path, index=False)
                logger.info(f"Saved subsample N={n} to {output_path}")

        except Exception as e:
            logger.error(f"Failed to process {dataset_name}: {e}")
            continue

    logger.info("Subsampling complete.")

if __name__ == "__main__":
    main()
