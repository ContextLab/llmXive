"""
Data filtering module for the gut microbiome study.
Implements cohort filtering, zero-variance checks, and listwise deletion.
"""
import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np

from src.utils.config import get_logs_dir, get_processed_data_dir
from src.utils.validation import load_schema, validate_dataframe_against_schema

# Configure logger specific to this module
logger = logging.getLogger(__name__)

# Covariates strictly defined in the schema for listwise deletion
COVARIATES = ['age', 'sex', 'bmi', 'dietary_fiber', 'antibiotic_use']
REQUIRED_METRICS = ['cognitive_flexibility_score', 'shannon_diversity']

def check_zero_variance(df: pd.DataFrame, column: str) -> bool:
    """
    Check if a specific column has zero variance (constant value).

    Args:
        df: Input DataFrame
        column: Column name to check

    Returns:
        bool: True if variance is zero or column is constant, False otherwise
    """
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in DataFrame.")
        return True

    non_null_vals = df[column].dropna()
    if len(non_null_vals) == 0:
        return True

    # Check if all values are the same
    unique_count = non_null_vals.nunique()
    return unique_count <= 1

def filter_cohort(
    df: pd.DataFrame,
    min_age: int = 65,
    drop_missing_covariates: bool = True
) -> Tuple[pd.DataFrame, int]:
    """
    Filter the cohort based on age, non-null metrics, and listwise deletion of covariates.

    Logic:
    1. Filter for age >= min_age.
    2. Filter for non-null required metrics (cognitive_flexibility_score, shannon_diversity).
    3. If drop_missing_covariates is True, perform listwise deletion on the defined covariates.
    4. Log the count of dropped rows.

    Args:
        df: Input DataFrame containing the cohort
        min_age: Minimum age threshold (default 65)
        drop_missing_covariates: Whether to drop rows with missing covariate values

    Returns:
        Tuple[pd.DataFrame, int]: Filtered DataFrame and count of rows dropped due to missing covariates
    """
    logger.info(f"Starting cohort filtering. Initial shape: {df.shape}")
    initial_count = len(df)

    # 1. Filter by age
    df = df[df['age'] >= min_age].copy()
    logger.info(f"After age filter (>= {min_age}): {len(df)} rows")

    # 2. Filter by non-null required metrics
    for col in REQUIRED_METRICS:
        if col in df.columns:
            before = len(df)
            df = df[df[col].notna()]
            logger.info(f"After filtering nulls for '{col}': {len(df)} rows (dropped {before - len(df)})")
        else:
            logger.warning(f"Required metric column '{col}' not found in DataFrame.")

    dropped_covariate_count = 0

    # 3. Listwise deletion for covariates
    if drop_missing_covariates:
        logger.info(f"Performing listwise deletion for covariates: {COVARIATES}")
        # Identify columns to check for missingness
        cols_to_check = [c for c in COVARIATES if c in df.columns]
        missing_cols = [c for c in COVARIATES if c not in df.columns]

        if missing_cols:
            logger.warning(f"Missing covariate columns in dataset (will not check for nulls): {missing_cols}")

        if cols_to_check:
            before = len(df)
            # Drop rows where ANY of the specified covariates are NaN
            df = df.dropna(subset=cols_to_check)
            dropped_covariate_count = before - len(df)
            logger.info(f"Listwise deletion dropped {dropped_covariate_count} rows due to missing covariates.")
        else:
            logger.warning("No covariate columns found to perform listwise deletion.")

    final_count = len(df)
    logger.info(f"Filtering complete. Final shape: {df.shape}. Total dropped: {initial_count - final_count}")
    if dropped_covariate_count > 0:
        logger.info(f"Rows dropped specifically due to missing covariates: {dropped_covariate_count}")

    return df, dropped_covariate_count

def main():
    """
    Main entry point to run filtering on the synthetic dataset and save results.
    """
    # Setup logging to file
    logs_dir = get_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "filtering.log"

    # Configure file handler for this specific log
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    # Ensure we don't duplicate handlers if re-running
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    # Load input data (expected from T010/T008)
    processed_dir = get_processed_data_dir()
    input_path = processed_dir / "merged_cohort.csv" # Assuming T010 output
    
    # Fallback if T010 output name differs, check raw for synthetic
    if not input_path.exists():
        input_path = get_logs_dir().parent / "data" / "raw" / "synthetic_data.csv"
        
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Ensure T008/T010 have run.")
        sys.exit(1)

    logger.info(f"Loading data from: {input_path}")
    df = pd.read_csv(input_path)

    # Run filtering
    filtered_df, dropped_count = filter_cohort(df, min_age=65, drop_missing_covariates=True)

    # Save output
    output_path = processed_dir / "filtered_cohort.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Filtered cohort saved to: {output_path}")

    # Log the specific count required by T013
    logger.info(f"T013 Summary: Listwise deletion dropped {dropped_count} rows.")

    return filtered_df

if __name__ == "__main__":
    main()