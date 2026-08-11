"""
Filtering module for the gut microbiome and cognitive flexibility study.

This module implements the filtering logic required for User Story 1:
- Filter for age >= 65
- Exclude rows with null Shannon diversity or cognitive scores
- Ensure required covariates (age, sex, BMI, fiber, antibiotics) are present and non-null
- Handle zero-variance datasets
- Support listwise deletion or mean imputation for missing covariates
"""

import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, List

import pandas as pd
import numpy as np

# Import paths from config
from code.src.utils.config import DATA_DIR, LOGS_DIR

# Ensure logging is configured
LOG_FILE = LOGS_DIR / "filtering.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

REQUIRED_COVARIATES = ['age', 'sex', 'BMI', 'fiber', 'antibiotics']
REQUIRED_SCORES = ['shannon_diversity', 'cognitive_score']
AGE_THRESHOLD = 65

def check_zero_variance(df: pd.DataFrame, column: str) -> bool:
    """
    Check if a column has zero variance (all values identical).

    Args:
        df: Input DataFrame
        column: Column name to check

    Returns:
        True if zero variance, False otherwise
    """
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in DataFrame.")
        return True  # Treat missing as zero variance for safety

    unique_vals = df[column].nunique()
    is_zero_var = unique_vals <= 1
    if is_zero_var:
        logger.warning(f"Column '{column}' has zero variance (unique values: {unique_vals}).")
    return is_zero_var

def filter_cohort(
    df: pd.DataFrame,
    impute_missing: bool = False
) -> Tuple[pd.DataFrame, dict]:
    """
    Filter the cohort based on age, non-null scores, and required covariates.

    This function performs the following steps:
    1. Filter for age >= 65
    2. Drop rows with null Shannon diversity or cognitive scores
    3. Drop rows with missing required covariates (or impute if requested)
    4. Check for zero-variance in critical columns and log warnings

    Args:
        df: Input DataFrame containing merged cohort data
        impute_missing: If True, use mean imputation for missing covariates.
                       If False (default), use listwise deletion.

    Returns:
        Tuple of (filtered DataFrame, statistics dictionary)
    """
    logger.info("Starting cohort filtering...")
    stats = {
        'initial_rows': len(df),
        'after_age_filter': 0,
        'after_null_scores': 0,
        'after_covariate_filter': 0,
        'final_rows': 0,
        'imputed_columns': [],
        'dropped_rows_reason': {}
    }

    # Step 1: Filter by age
    logger.info(f"Filtering for age >= {AGE_THRESHOLD}")
    initial_count = len(df)
    df = df[df['age'] >= AGE_THRESHOLD].copy()
    stats['after_age_filter'] = len(df)
    dropped_age = initial_count - stats['after_age_filter']
    stats['dropped_rows_reason']['age_filter'] = dropped_age
    logger.info(f"Dropped {dropped_age} rows due to age < {AGE_THRESHOLD}")

    # Step 2: Drop rows with null scores
    logger.info("Dropping rows with null Shannon diversity or cognitive scores")
    initial_count = len(df)
    df = df.dropna(subset=REQUIRED_SCORES)
    stats['after_null_scores'] = len(df)
    dropped_scores = initial_count - stats['after_null_scores']
    stats['dropped_rows_reason']['null_scores'] = dropped_scores
    logger.info(f"Dropped {dropped_scores} rows due to null scores")

    # Step 3: Handle missing covariates
    logger.info("Handling missing covariates")
    missing_covariates = df[REQUIRED_COVARIATES].isna().any(axis=1)
    if impute_missing:
        logger.info("Using mean imputation for missing covariates")
        imputed_cols = []
        for col in REQUIRED_COVARIATES:
            if col in df.columns:
                if df[col].isna().any():
                    mean_val = df[col].mean()
                    df[col] = df[col].fillna(mean_val)
                    imputed_cols.append(col)
        stats['imputed_columns'] = imputed_cols
        logger.info(f"Imputed missing values in columns: {imputed_cols}")
    else:
        logger.info("Using listwise deletion for missing covariates")
        initial_count = len(df)
        df = df.dropna(subset=REQUIRED_COVARIATES)
        stats['after_covariate_filter'] = len(df)
        dropped_cov = initial_count - stats['after_covariate_filter']
        stats['dropped_rows_reason']['missing_covariates'] = dropped_cov
        logger.info(f"Dropped {dropped_cov} rows due to missing covariates")

    # Step 4: Check for zero variance in critical columns
    critical_cols = REQUIRED_SCORES + REQUIRED_COVARIATES
    for col in critical_cols:
        if col in df.columns:
            check_zero_variance(df, col)

    stats['final_rows'] = len(df)
    logger.info(f"Filtering complete. Final cohort size: {stats['final_rows']}")
    logger.info(f"Total dropped rows: {stats['initial_rows'] - stats['final_rows']}")

    return df, stats

def main():
    """
    Main entry point for the filtering script.

    Reads the merged cohort from data/processed/merged_cohort.csv,
    applies filtering, and saves the result to data/processed/filtered_cohort.csv.
    """
    input_path = DATA_DIR / "processed" / "merged_cohort.csv"
    output_path = DATA_DIR / "processed" / "filtered_cohort.csv"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run data ingestion first to generate the merged cohort.")
        sys.exit(1)

    logger.info(f"Reading input from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")

    # Apply filtering with listwise deletion (default)
    # Can be changed to impute_missing=True if needed
    filtered_df, stats = filter_cohort(df, impute_missing=False)

    # Save filtered cohort
    logger.info(f"Saving filtered cohort to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(filtered_df)} rows to {output_path}")

    # Log statistics
    logger.info("Filtering Statistics:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    return filtered_df, stats

if __name__ == "__main__":
    main()
