import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, List

import pandas as pd
import numpy as np

from code.src.utils.config import LOGS_DIR, PROCESSED_DATA_DIR, ensure_directories

# Configure logging for this module
logger = logging.getLogger(__name__)

def check_zero_variance(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[List[str], bool]:
    """
    Check for zero-variance columns in the DataFrame.
    
    A column has zero variance if it contains only a single unique value 
    (or is empty/NaN-only), which would cause correlation calculations to fail 
    or produce undefined results.
    
    Args:
        df: The DataFrame to check.
        columns: Optional list of specific columns to check. If None, checks 
               all numeric columns.
    
    Returns:
        Tuple of (list of zero-variance column names, boolean indicating 
        if any zero-variance columns were found).
    """
    if columns is None:
        # Select only numeric columns for variance check
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    zero_var_cols = []
    
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column '{col}' not found in DataFrame, skipping.")
            continue
        
        # Drop NaN values for variance calculation
        non_null_vals = df[col].dropna()
        
        if len(non_null_vals) == 0:
            # All values are NaN - effectively zero variance
            zero_var_cols.append(col)
            logger.debug(f"Column '{col}' has no non-null values (zero variance).")
            continue
        
        # Check if there's only one unique value
        unique_count = non_null_vals.nunique()
        if unique_count <= 1:
            zero_var_cols.append(col)
            logger.debug(f"Column '{col}' has only {unique_count} unique value(s) (zero variance).")
    
    return zero_var_cols, len(zero_var_cols) > 0

def filter_cohort(
    df: pd.DataFrame,
    min_age: int = 65,
    required_columns: Optional[List[str]] = None,
    target_metrics: Optional[List[str]] = None,
    imputation_strategy: str = 'listwise'
) -> Tuple[pd.DataFrame, dict]:
    """
    Filter the cohort based on age, non-null metrics, and required covariates.
    
    This function also checks for zero-variance datasets and flags them to 
    prevent downstream correlation analysis from failing.
    
    Args:
        df: The merged cohort DataFrame.
        min_age: Minimum age threshold (default 65).
        required_columns: List of required covariate columns (age, sex, BMI, fiber, antibiotics).
        target_metrics: List of target metric columns (Shannon, Cognitive scores) to check for nulls.
        imputation_strategy: Strategy for missing covariates ('listwise' or 'mean').
    
    Returns:
        Tuple of (filtered DataFrame, metadata dict with filtering stats and flags).
    """
    logger.info(f"Starting cohort filtering with min_age={min_age}")
    
    if required_columns is None:
        required_columns = ['age', 'sex', 'bmi', 'fiber_intake', 'antibiotics_use']
    
    if target_metrics is None:
        target_metrics = ['shannon_diversity', 'cognitive_score']
    
    metadata = {
        'initial_rows': len(df),
        'final_rows': 0,
        'rows_dropped_age': 0,
        'rows_dropped_null_metrics': 0,
        'rows_dropped_null_covariates': 0,
        'zero_variance_detected': False,
        'zero_variance_columns': [],
        'imputation_applied': False,
        'imputation_strategy': imputation_strategy
    }
    
    # 1. Filter by age
    if 'age' in df.columns:
        initial_count = len(df)
        df = df[df['age'] >= min_age]
        metadata['rows_dropped_age'] = initial_count - len(df)
        logger.info(f"Dropped {metadata['rows_dropped_age']} rows with age < {min_age}")
    else:
        logger.warning("Age column not found in dataset. Skipping age filter.")
    
    # 2. Handle missing covariates
    missing_covariates = []
    for col in required_columns:
        if col not in df.columns:
            logger.warning(f"Required covariate '{col}' not found in dataset.")
            missing_covariates.append(col)
    
    if missing_covariates:
        logger.error(f"Missing required covariates: {missing_covariates}")
        metadata['rows_dropped_null_covariates'] = len(df)
        df = df[[]]  # Return empty dataframe
        return df, metadata
    
    # Apply imputation or listwise deletion for missing covariates
    if imputation_strategy == 'mean':
        for col in required_columns:
            if df[col].isna().any():
                mean_val = df[col].mean()
                df[col] = df[col].fillna(mean_val)
                metadata['imputation_applied'] = True
                logger.info(f"Applied mean imputation for '{col}' (mean={mean_val:.4f})")
    elif imputation_strategy == 'listwise':
        initial_count = len(df)
        df = df.dropna(subset=required_columns)
        dropped = initial_count - len(df)
        metadata['rows_dropped_null_covariates'] = dropped
        if dropped > 0:
            logger.info(f"Dropped {dropped} rows due to missing covariates (listwise deletion)")
    else:
        raise ValueError(f"Unknown imputation_strategy: {imputation_strategy}")
    
    # 3. Filter by target metrics (Shannon, Cognitive scores)
    initial_count = len(df)
    df = df.dropna(subset=target_metrics)
    metadata['rows_dropped_null_metrics'] = initial_count - len(df)
    if metadata['rows_dropped_null_metrics'] > 0:
        logger.info(f"Dropped {metadata['rows_dropped_null_metrics']} rows due to missing target metrics")
    
    # 4. Check for zero-variance in target metrics and covariates
    check_cols = target_metrics + required_columns
    zero_var_cols, has_zero_var = check_zero_variance(df, columns=check_cols)
    
    metadata['zero_variance_detected'] = has_zero_var
    metadata['zero_variance_columns'] = zero_var_cols
    
    if has_zero_var:
        logger.warning(f"Zero-variance detected in columns: {zero_var_cols}")
        logger.warning("Correlation analysis will be skipped for zero-variance columns.")
        # Flag the dataset but do not drop rows yet - the analysis step will handle skipping
    
    metadata['final_rows'] = len(df)
    logger.info(f"Cohort filtering complete. Final rows: {len(df)} (from {metadata['initial_rows']})")
    
    return df, metadata

def main():
    """
    Main entry point for the filtering script.
    
    Loads the merged synthetic cohort from data/processed/, applies filtering
    logic, and saves the filtered cohort to data/processed/filtered_cohort.csv.
    Also logs metadata about the filtering process.
    """
    ensure_directories()
    
    input_path = PROCESSED_DATA_DIR / "merged_cohort.csv"
    output_path = PROCESSED_DATA_DIR / "filtered_cohort.csv"
    log_path = LOGS_DIR / "filtering.log"
    
    # Setup file logging
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    logger.info("=" * 60)
    logger.info("Starting filtering pipeline")
    logger.info("=" * 60)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run ingestion/synthetic generation first.")
        sys.exit(1)
    
    # Load data
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)
    
    # Run filtering
    filtered_df, metadata = filter_cohort(
        df,
        min_age=65,
        required_columns=['age', 'sex', 'bmi', 'fiber_intake', 'antibiotics_use'],
        target_metrics=['shannon_diversity', 'cognitive_score'],
        imputation_strategy='listwise'
    )
    
    # Save filtered cohort
    if len(filtered_df) > 0:
        filtered_df.to_csv(output_path, index=False)
        logger.info(f"Saved filtered cohort to {output_path} ({len(filtered_df)} rows)")
    else:
        logger.warning("No rows remaining after filtering. Saving empty file.")
        filtered_df.to_csv(output_path, index=False)
    
    # Log metadata summary
    logger.info("-" * 40)
    logger.info("Filtering Metadata Summary:")
    for key, value in metadata.items():
        logger.info(f"  {key}: {value}")
    logger.info("-" * 40)
    
    # Handle zero-variance case
    if metadata['zero_variance_detected']:
        logger.warning("ZERO-VARIANCE DETECTED!")
        logger.warning(f"Affected columns: {metadata['zero_variance_columns']}")
        logger.warning("Downstream correlation analysis MUST skip these columns or the entire analysis.")
        # We do not exit here, but the analysis step must check this flag
    
    logger.info("Filtering pipeline completed.")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()