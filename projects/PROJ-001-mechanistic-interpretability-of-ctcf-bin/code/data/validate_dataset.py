"""
Validation module for the unified CTCF dataset.
Ensures data integrity before downstream model training.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SEQUENCE_LENGTH = 1000  # Expected length of ±500bp windows
MIN_CHROMATIN_COLS = 3  # ATAC-seq, H3K27ac, and potentially others

def load_dataset(dataset_path: str) -> pd.DataFrame:
    """
    Load the unified dataset from a Parquet file.

    Args:
        dataset_path: Path to the .parquet file.

    Returns:
        pd.DataFrame: The loaded dataset.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    logger.info(f"Loading dataset from {dataset_path}")
    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def validate_sequence_length(df: pd.DataFrame, expected_length: int = SEQUENCE_LENGTH) -> bool:
    """
    Validates that every row in the 'sequence' column has the expected fixed length.

    Args:
        df: The dataframe to validate.
        expected_length: The expected length of the sequence (default 1000).

    Returns:
        bool: True if all sequences match the expected length.

    Raises:
        ValueError: If any sequence does not match the expected length.
    """
    if 'sequence' not in df.columns:
        logger.error("Column 'sequence' not found in dataset.")
        raise ValueError("Missing 'sequence' column in dataset.")

    # Check for non-string types or NaNs in sequence column first
    if df['sequence'].isna().any():
        null_count = df['sequence'].isna().sum()
        raise ValueError(f"Found {null_count} null values in 'sequence' column.")

    # Check lengths
    lengths = df['sequence'].str.len()
    invalid_mask = lengths != expected_length
    invalid_count = invalid_mask.sum()

    if invalid_count > 0:
        sample_indices = df[invalid_mask].index[:5].tolist()
        sample_lengths = df.loc[invalid_mask, 'sequence'].str.head(5).tolist()
        raise ValueError(
            f"Sequence length validation failed. "
            f"Expected length: {expected_length}, found {invalid_count} mismatches. "
            f"Sample indices: {sample_indices}, Sample lengths: {sample_lengths}"
        )

    logger.info(f"Sequence length validation passed: all {len(df)} rows have length {expected_length}.")
    return True

def validate_no_nulls(df: pd.DataFrame, critical_columns: Optional[List[str]] = None) -> bool:
    """
    Validates that critical columns contain no null values.

    Args:
        df: The dataframe to validate.
        critical_columns: List of column names that must not be null.
                         If None, defaults to 'sequence' and all numeric columns.

    Returns:
        bool: True if no nulls are found.

    Raises:
        ValueError: If nulls are found in critical columns.
    """
    if critical_columns is None:
        # Default: sequence + all numeric columns (chromatin signals)
        critical_columns = ['sequence'] + list(df.select_dtypes(include=[np.number]).columns)

    null_found = False
    for col in critical_columns:
        if col not in df.columns:
            logger.warning(f"Critical column '{col}' not found in dataset. Skipping null check.")
            continue

        null_count = df[col].isna().sum()
        if null_count > 0:
            null_found = True
            logger.error(f"Found {null_count} null values in column '{col}'.")

    if null_found:
        # Raise a comprehensive error
        null_summary = {
            col: df[col].isna().sum()
            for col in critical_columns
            if col in df.columns and df[col].isna().any()
        }
        raise ValueError(f"Null values detected in dataset: {null_summary}")

    logger.info("Null value validation passed: no nulls found in critical columns.")
    return True

def validate_chromatin_alignment(df: pd.DataFrame) -> bool:
    """
    Validates that chromatin signal columns are present and numeric.
    Ensures that for every sequence row, the corresponding chromatin data exists.

    Args:
        df: The dataframe to validate.

    Returns:
        bool: True if alignment is valid.

    Raises:
        ValueError: If chromatin columns are missing or misaligned.
    """
    # Identify potential chromatin columns (typically float/int, not 'sequence' or 'label')
    exclude_cols = {'sequence', 'label', 'peak_id', 'cell_type', 'chromosome', 'start', 'end'}
    chromatin_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in [np.float32, np.float64, np.int32, np.int64]]

    if len(chromatin_cols) < MIN_CHROMATIN_COLS:
        logger.warning(f"Found only {len(chromatin_cols)} numeric columns (expected >= {MIN_CHROMATIN_COLS}). "
                     "This might indicate missing ATAC-seq or histone data.")
        # Depending on strictness, we might raise here. For now, log and continue if > 0.
        if len(chromatin_cols) == 0:
            raise ValueError("No chromatin signal columns found. Dataset is invalid for training.")

    # Check for alignment: ensure no row has nulls in ANY chromatin column
    if not df[chromatin_cols].isna().any().any():
        logger.info(f"Chromatin alignment validation passed: {len(chromatin_cols)} signal columns are complete.")
        return True
    else:
        # Count rows with missing chromatin data
        missing_rows = df[chromatin_cols].isna().any(axis=1).sum()
        raise ValueError(f"Chromatin alignment failed: {missing_rows} rows have missing values in chromatin columns.")

def validate_dataset(dataset_path: str) -> bool:
    """
    Runs all validation checks on the dataset.

    Args:
        dataset_path: Path to the .parquet file.

    Returns:
        bool: True if all validations pass.

    Raises:
        ValueError: If any validation fails.
    """
    logger.info("Starting dataset validation pipeline...")

    # 1. Load
    df = load_dataset(dataset_path)

    # 2. Sequence Length
    validate_sequence_length(df)

    # 3. Null Values
    validate_no_nulls(df)

    # 4. Chromatin Alignment
    validate_chromatin_alignment(df)

    logger.info("Dataset validation completed successfully.")
    return True

def main():
    """
    Entry point for the validation script.
    Expects the dataset path as a command-line argument or uses the default.
    """
    # Default path based on project structure
    default_path = "data/processed/unified_ctcf_dataset.parquet"
    
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = default_path
        logger.warning(f"No path provided, using default: {dataset_path}")

    try:
        success = validate_dataset(dataset_path)
        if success:
            logger.info("Validation PASSED. Dataset is ready for training.")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Validation FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
