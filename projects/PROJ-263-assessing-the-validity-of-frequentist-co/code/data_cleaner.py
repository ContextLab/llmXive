"""
Data cleaner module for UCI dataset preprocessing.

Implements FR-002: Filter for continuous variables and exclude rows with missing values.
Implements Edge Cases: Handle insufficient row counts and invalid data types.
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd

from config import get_data_dir, get_log_level
from data_loader import identify_continuous_variables

# Configure logging
logging.basicConfig(
    level=get_log_level(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows containing any missing values (NaN).

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with rows containing NaN removed.
    """
    original_count = len(df)
    cleaned_df = df.dropna()
    removed_count = original_count - len(cleaned_df)

    if removed_count > 0:
        logger.info(f"Removed {removed_count} rows with missing values ({removed_count/original_count*100:.2f}%).")
    else:
        logger.info("No missing values found.")

    return cleaned_df


def filter_continuous_variables(
    df: pd.DataFrame,
    continuous_vars: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter DataFrame to include only continuous numeric variables.

    If `continuous_vars` is not provided, it attempts to identify them automatically
    using `data_loader.identify_continuous_variables`.

    Args:
        df: Input DataFrame.
        continuous_vars: Optional list of column names known to be continuous.

    Returns:
        Tuple of (filtered DataFrame, list of continuous variable names used).
    """
    if continuous_vars is None:
        logger.info("Identifying continuous variables automatically...")
        continuous_vars = identify_continuous_variables(df)

    if not continuous_vars:
        logger.warning("No continuous variables found in the dataset.")
        return pd.DataFrame(), []

    # Filter columns
    available_cols = [col for col in continuous_vars if col in df.columns]
    missing_cols = [col for col in continuous_vars if col not in df.columns]

    if missing_cols:
        logger.warning(f"Continuous variables not found in data: {missing_cols}")

    if not available_cols:
        logger.error("No valid continuous variables remain after filtering.")
        return pd.DataFrame(), []

    filtered_df = df[available_cols].copy()

    # Ensure all selected columns are numeric
    non_numeric_cols = []
    for col in available_cols:
        if not pd.api.types.is_numeric_dtype(filtered_df[col]):
            # Attempt conversion
            try:
                filtered_df[col] = pd.to_numeric(filtered_df[col], errors='raise')
            except (ValueError, TypeError):
                non_numeric_cols.append(col)

    if non_numeric_cols:
        logger.warning(f"Non-numeric columns after filtering (dropping): {non_numeric_cols}")
        filtered_df = filtered_df.drop(columns=non_numeric_cols)

    logger.info(f"Filtered to continuous variables: {list(filtered_df.columns)}")
    return filtered_df, list(filtered_df.columns)


def validate_dataset_sufficiency(
    df: pd.DataFrame,
    min_rows: int = 10
) -> bool:
    """
    Validate that the dataset has enough rows for simulation.

    Args:
        df: Input DataFrame.
        min_rows: Minimum required rows.

    Returns:
        True if sufficient, False otherwise.
    """
    if len(df) < min_rows:
        logger.error(f"Dataset has only {len(df)} rows, which is less than required {min_rows}.")
        return False
    return True


def clean_dataset_for_simulation(
    dataset_path: str,
    continuous_vars: Optional[List[str]] = None,
    min_rows: int = 10
) -> Optional[pd.DataFrame]:
    """
    Main entry point to clean a dataset for simulation.

    Steps:
    1. Load raw data.
    2. Filter continuous variables.
    3. Drop missing values.
    4. Validate row count.

    Args:
        dataset_path: Path to the raw dataset file.
        continuous_vars: Optional list of continuous variable names.
        min_rows: Minimum rows required.

    Returns:
        Cleaned DataFrame or None if validation fails.
    """
    logger.info(f"Starting cleaning process for: {dataset_path}")

    # Load data
    if not os.path.exists(dataset_path):
        logger.error(f"File not found: {dataset_path}")
        return None

    try:
        # Try loading with pandas, inferring delimiter
        df = pd.read_csv(dataset_path)
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_path}: {e}")
        return None

    # Step 1: Filter continuous variables
    df, used_vars = filter_continuous_variables(df, continuous_vars)
    if df.empty:
        logger.error("No continuous variables available after filtering.")
        return None

    # Step 2: Clean missing values
    df = clean_missing_values(df)

    # Step 3: Validate sufficiency
    if not validate_dataset_sufficiency(df, min_rows):
        return None

    logger.info(f"Dataset cleaned successfully. Shape: {df.shape}")
    return df


def main():
    """
    CLI entry point for testing the data cleaner.
    Expects a dataset path as the first argument.
    """
    import sys
    if len(sys.argv) < 2:
        print("Usage: python code/data_cleaner.py <path_to_dataset>")
        sys.exit(1)

    path = sys.argv[1]
    cleaned = clean_dataset_for_simulation(path)

    if cleaned is not None:
        print(f"Cleaning successful. Rows: {len(cleaned)}, Cols: {len(cleaned.columns)}")
        print(cleaned.head())
    else:
        print("Cleaning failed or dataset insufficient.")
        sys.exit(1)


if __name__ == "__main__":
    main()