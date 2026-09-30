import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np

from code.src.utils.config import get_logs_dir, ensure_directories

# Configure logger for this module
logger = logging.getLogger(__name__)

def check_zero_variance(df: pd.DataFrame, columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if any specified columns in the dataframe have zero variance (constant values).
    
    Args:
        df: The dataframe to check.
        columns: List of column names to check for zero variance.
    
    Returns:
        Tuple containing:
            - Boolean: True if any zero-variance columns are found, False otherwise.
            - List of column names that have zero variance.
    """
    zero_variance_cols = []
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column '{col}' not found in dataframe. Skipping variance check.")
            continue
        
        # Check for constant values (variance == 0)
        # Handle non-numeric columns by checking unique values
        if pd.api.types.is_numeric_dtype(df[col]):
            variance = df[col].var()
            if pd.isna(variance) or variance == 0:
                zero_variance_cols.append(col)
                logger.warning(f"Column '{col}' has zero variance (constant value).")
        else:
            # For non-numeric, check if all values are the same
            unique_values = df[col].ndropna()
            if unique_values <= 1:
                zero_variance_cols.append(col)
                logger.warning(f"Column '{col}' has zero variance (constant value).")
    
    has_zero_variance = len(zero_variance_cols) > 0
    return has_zero_variance, zero_variance_cols

def filter_cohort(
    df: pd.DataFrame,
    age_threshold: int = 65,
    required_columns: Optional[List[str]] = None,
    check_variance: bool = True,
    variance_columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, bool, List[str]]:
    """
    Filter the cohort based on age, non-null values, and optionally zero-variance checks.
    
    Args:
        df: Input dataframe.
        age_threshold: Minimum age for inclusion (default 65).
        required_columns: List of columns that must be non-null.
        check_variance: Whether to check for zero-variance columns.
        variance_columns: Specific columns to check for zero variance.
    
    Returns:
        Tuple containing:
            - Filtered dataframe.
            - Boolean: True if zero-variance was detected and skipped, False otherwise.
            - List of zero-variance columns detected (if any).
    """
    if required_columns is None:
        required_columns = [
            'age', 'sex', 'bmi', 'dietary_fiber', 'antibiotic_use',
            'cognitive_flexibility_score', 'shannon_diversity'
        ]
    
    if variance_columns is None:
        variance_columns = [
            'cognitive_flexibility_score', 'shannon_diversity', 
            'simpson_diversity', 'chao1'
        ]
    
    ensure_directories()
    logs_dir = get_logs_dir()
    logger.info(f"Starting cohort filtering. Logs will be written to {logs_dir}")
    
    # Step 1: Filter by age
    initial_count = len(df)
    df = df[df['age'] >= age_threshold]
    logger.info(f"Age filter (>= {age_threshold}): {initial_count} -> {len(df)} rows")
    
    # Step 2: Filter by non-null required columns (Listwise deletion)
    df = df.dropna(subset=required_columns)
    logger.info(f"Non-null filter on {len(required_columns)} columns: {len(df)} rows remaining")
    
    # Step 3: Check for zero-variance in critical analysis columns
    if check_variance:
        has_zero_var, zero_var_cols = check_zero_variance(df, variance_columns)
        if has_zero_var:
            logger.warning(
                f"Zero-variance detected in columns: {zero_var_cols}. "
                "Correlation analysis will be skipped for these metrics."
            )
            return df, True, zero_var_cols
        logger.info("No zero-variance detected in analysis columns.")
    
    return df, False, []

def main():
    """
    Main entry point for filtering synthetic cohort data.
    Reads from data/raw/synthetic_data.csv and writes to data/processed/filtered_cohort.csv.
    """
    from code.src.utils.config import get_raw_data_dir, get_processed_data_dir
    
    raw_dir = get_raw_data_dir()
    processed_dir = get_processed_data_dir()
    
    input_path = raw_dir / "synthetic_data.csv"
    output_path = processed_dir / "filtered_cohort.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows")
    
    # Perform filtering
    filtered_df, skipped, skipped_cols = filter_cohort(df)
    
    # Save results
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered cohort to {output_path} ({len(filtered_df)} rows)")
    
    if skipped:
        logger.warning(f"Zero-variance detected in: {skipped_cols}. "
                       "Downstream correlation analysis must handle this flag.")
    
    return filtered_df, skipped, skipped_cols

if __name__ == "__main__":
    # Setup logging to file and console
    from code.src.utils.config import setup_logging
    setup_logging()
    
    main()
    logger.info("Filtering complete.")