"""
Imputation Orchestrator for Heusler Alloy Data.

Implements Spec FR-002:
- Calculate missing rate per column.
- If missing rate > 15%: Perform listwise deletion (drop rows with any missing values in that column).
- If missing rate <= 15%: Perform mean imputation.
- MICE is explicitly excluded.
"""
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from src.utils.logging_config import setup_logging

# Configure logger
logger = setup_logging(__name__)


def calculate_missing_rates(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate the missing rate (proportion of NaN) for each specified column.

    Args:
        df: Input DataFrame.
        columns: List of column names to check. If None, checks all numeric columns.

    Returns:
        Dictionary mapping column name to missing rate (0.0 to 1.0).
    """
    if columns is None:
        # Only check numeric columns for imputation logic
        columns = df.select_dtypes(include=[np.number]).columns.tolist()

    rates = {}
    for col in columns:
        total = df[col].count()
        missing = df[col].isna().sum()
        if total == 0:
            rates[col] = 1.0
        else:
            rates[col] = missing / total
    return rates


def perform_mean_imputation(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Perform mean imputation for specified columns.

    Args:
        df: Input DataFrame.
        columns: List of columns to impute.

    Returns:
        DataFrame with mean-imputed values.
    """
    df_imputed = df.copy()
    for col in columns:
        if df_imputed[col].isna().any():
            mean_val = df_imputed[col].mean()
            if pd.isna(mean_val):
                # If all values are NaN, fill with 0.0 or raise?
                # Per spec, if >15% we drop. If <=15% and mean is NaN (all NaN),
                # we can't impute. We'll fill with 0.0 but log a warning.
                logger.warning(f"Column {col} has all NaN values. Filling with 0.0.")
                mean_val = 0.0
            df_imputed[col] = df_imputed[col].fillna(mean_val)
    return df_imputed


def perform_listwise_deletion(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Perform listwise deletion: remove any row that has a missing value in any of the specified columns.

    Args:
        df: Input DataFrame.
        columns: List of columns to check for missing values.

    Returns:
        DataFrame with rows containing missing values in specified columns removed.
    """
    df_cleaned = df.dropna(subset=columns, how='any')
    dropped_count = len(df) - len(df_cleaned)
    if dropped_count > 0:
        logger.info(f"Listwise deletion: Dropped {dropped_count} rows due to missing values in {columns}.")
    return df_cleaned


def orchestrate_imputation(
    df: pd.DataFrame,
    threshold: float = 0.15,
    columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Main orchestration function for handling missing data per Spec FR-002.

    Logic:
    1. Calculate missing rates for relevant columns.
    2. Identify columns with rate > threshold (High Missing) and <= threshold (Low Missing).
    3. For High Missing columns: Perform listwise deletion on the dataframe.
       Note: We must apply this deletion first, or the mean imputation on low-missing
       columns would be skewed by the rows we intend to delete?
       Actually, standard practice:
       - If a column has >15% missing, we drop rows where THAT column is missing.
       - If a column has <=15% missing, we impute.
       However, if we drop rows for High Missing columns, the dataset shrinks.
       Then we impute the remaining rows for Low Missing columns.

    Args:
        df: Input DataFrame.
        threshold: Missing rate threshold (default 0.15).
        columns: Specific columns to process. If None, processes all numeric columns.

    Returns:
        Tuple of (processed DataFrame, action_log dict mapping column -> action taken).
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df, {}

    rates = calculate_missing_rates(df, columns)
    logger.info(f"Missing rates calculated: {rates}")

    high_missing_cols = [col for col, rate in rates.items() if rate > threshold]
    low_missing_cols = [col for col, rate in rates.items() if rate <= threshold]

    action_log = {}

    # Step 1: Handle High Missing Columns (>15%) via Listwise Deletion
    if high_missing_cols:
        logger.warning(f"Columns with >{threshold*100}% missing data: {high_missing_cols}. "
                       f"Performing listwise deletion.")
        df = perform_listwise_deletion(df, high_missing_cols)
        for col in high_missing_cols:
            action_log[col] = "listwise_deletion"
    else:
        logger.info(f"No columns exceeded the {threshold*100}% missing threshold.")

    # Step 2: Handle Low Missing Columns (<=15%) via Mean Imputation
    # Note: We only impute columns that still have missing values after deletion
    # and were in the low_missing_cols list.
    if low_missing_cols:
        # Re-calculate rates or just check if any are still NaN?
        # We only care about columns in low_missing_cols.
        cols_to_impute = [col for col in low_missing_cols if df[col].isna().any()]
        if cols_to_impute:
            logger.info(f"Columns with <={threshold*100}% missing data: {cols_to_impute}. "
                        f"Performing mean imputation.")
            df = perform_mean_imputation(df, cols_to_impute)
            for col in cols_to_impute:
                action_log[col] = "mean_imputation"
        else:
            logger.info("No low-missing columns had remaining NaN values after deletion.")
    else:
        logger.info("No columns fell into the <=15% missing category.")

    # Verify no NaNs remain in the processed columns (unless the whole column was dropped)
    final_rates = calculate_missing_rates(df, columns)
    if any(r > 0 for r in final_rates.values()):
        logger.warning("Some columns still contain NaN values after imputation process.")
        for col, rate in final_rates.items():
            if rate > 0:
                logger.warning(f"Column {col} still has {rate:.2%} missing values.")
    else:
        logger.info("All targeted columns have been successfully processed (no NaNs remaining).")

    return df, action_log


def main():
    """
    Example usage for CLI testing or pipeline integration.
    Expects input file path as argument or uses default.
    """
    import sys

    # Default paths for demonstration if run directly
    input_path = Path("data/processed/alloys_raw.csv")
    output_path = Path("data/processed/alloys_imputed.csv")

    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} rows. Columns: {df.columns.tolist()}")

    # Identify numeric columns for imputation (excluding IDs, strings, etc.)
    # We assume the pipeline has already standardized units and types.
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        logger.warning("No numeric columns found to impute.")
        # Save as is
        df.to_csv(output_path, index=False)
        logger.info(f"Saved unmodified data to {output_path}")
        return

    logger.info(f"Processing missing data for columns: {numeric_cols}")

    processed_df, actions = orchestrate_imputation(df, threshold=0.15, columns=numeric_cols)

    logger.info(f"Imputation actions taken: {actions}")
    logger.info(f"Final dataset shape: {processed_df.shape}")

    # Save results
    processed_df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved imputed data to {output_path}")


if __name__ == "__main__":
    main()