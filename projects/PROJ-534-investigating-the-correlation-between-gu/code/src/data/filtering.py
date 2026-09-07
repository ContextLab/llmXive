import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/filtering.log')
    ]
)
logger = logging.getLogger(__name__)

def check_zero_variance(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    """
    Check if any numeric columns in the DataFrame have zero variance (constant values).
    
    Args:
        df: Input DataFrame
        columns: List of specific columns to check. If None, checks all numeric columns.
    
    Returns:
        Tuple of (has_zero_variance, list_of_zero_variance_columns)
    """
    if columns is None:
        # Select only numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        columns_to_check = [col for col in numeric_cols if col in df.columns]
    else:
        columns_to_check = [col for col in columns if col in df.columns]
    
    zero_variance_cols = []
    
    for col in columns_to_check:
        if col in df.columns:
            # Check if all values are the same (variance == 0)
            # Also handle cases where all values might be NaN
            if df[col].nunique() <= 1:
                zero_variance_cols.append(col)
    
    has_zero_variance = len(zero_variance_cols) > 0
    return has_zero_variance, zero_variance_cols

def filter_cohort(
    df: pd.DataFrame,
    min_age: int = 65,
    required_metrics: Optional[List[str]] = None,
    required_covariates: Optional[List[str]] = None,
    handle_missing: str = 'listwise',
    check_variance: bool = True,
    variance_columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, bool, List[str]]:
    """
    Filter the cohort based on age, missing values, and zero-variance checks.
    
    Args:
        df: Input DataFrame with merged cohort data
        min_age: Minimum age for inclusion (default: 65)
        required_metrics: List of required metric columns (e.g., Shannon, cognitive scores)
        required_covariates: List of required covariate columns (e.g., age, sex, BMI, fiber, antibiotics)
        handle_missing: How to handle missing values ('listwise' or 'impute')
        check_variance: Whether to check for zero-variance columns
        variance_columns: Specific columns to check for zero variance. If None, checks all numeric columns.
    
    Returns:
        Tuple of (filtered_df, skipped_due_to_zero_variance, zero_variance_columns)
    """
    logger.info(f"Starting cohort filtering with min_age={min_age}")
    
    # Apply age filter
    if 'age' in df.columns:
        initial_count = len(df)
        df = df[df['age'] >= min_age]
        logger.info(f"Age filter applied: {initial_count} -> {len(df)} participants (age >= {min_age})")
    else:
        logger.warning("Age column not found in dataset, skipping age filter")
    
    # Define required columns
    if required_metrics is None:
        required_metrics = []
    if required_covariates is None:
        required_covariates = []
    
    all_required_cols = required_metrics + required_covariates
    
    # Handle missing values
    if handle_missing == 'listwise':
        initial_count = len(df)
        # Drop rows with any NaN in required columns
        if all_required_cols:
            df = df.dropna(subset=all_required_cols)
        else:
            # If no specific columns defined, drop rows with any NaN in numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            df = df.dropna(subset=numeric_cols)
        
        dropped_count = initial_count - len(df)
        if dropped_count > 0:
            logger.info(f"Listwise deletion: {dropped_count} rows removed due to missing values")
    elif handle_missing == 'impute':
        # Mean imputation for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in numeric_cols:
            if col in df.columns and df[col].isna().any():
                mean_val = df[col].mean()
                df[col] = df[col].fillna(mean_val)
                logger.info(f"Imputed {df[col].isna().sum()} missing values in {col} with mean {mean_val:.4f}")
    else:
        raise ValueError(f"Unknown handle_missing option: {handle_missing}. Use 'listwise' or 'impute'")
    
    # Check for zero variance
    skipped_due_to_zero_variance = False
    zero_variance_cols = []
    
    if check_variance:
        has_zero_var, zero_variance_cols = check_zero_variance(df, variance_columns)
        
        if has_zero_var:
            skipped_due_to_zero_variance = True
            logger.warning(f"Zero-variance detected in columns: {zero_variance_cols}")
            logger.warning("Correlation analysis will be skipped for this dataset due to zero variance")
            logger.warning("This indicates a lack of variability in the data, making correlation analysis invalid")
    
    logger.info(f"Final cohort size: {len(df)} participants")
    
    return df, skipped_due_to_zero_variance, zero_variance_cols

def main():
    """
    Main function to run the filtering pipeline.
    This is typically called from a script or pipeline orchestration.
    """
    from code.src.utils.config import DATA_DIR, PROCESSED_DATA_DIR, ensure_directories, set_global_seed
    from code.src.data.ingestion import merge_datasets
    
    # Setup
    set_global_seed()
    ensure_directories()
    
    # Load merged data
    logger.info("Loading merged cohort data...")
    try:
        df = merge_datasets()
        logger.info(f"Loaded {len(df)} records from merged data")
    except FileNotFoundError as e:
        logger.error(f"Merged data file not found: {e}")
        logger.error("Please run synthetic generation and ingestion first (T011, T012)")
        sys.exit(1)
    
    # Define required columns based on the study design
    required_metrics = ['shannon_diversity', 'cognitive_flexibility_score']
    required_covariates = ['age', 'sex', 'bmi', 'fiber_intake', 'antibiotics_use']
    
    # Filter cohort
    filtered_df, skipped, zero_var_cols = filter_cohort(
        df,
        min_age=65,
        required_metrics=required_metrics,
        required_covariates=required_covariates,
        handle_missing='listwise',
        check_variance=True,
        variance_columns=required_metrics + required_covariates
    )
    
    # Save filtered cohort
    output_path = PROCESSED_DATA_DIR / "filtered_cohort.csv"
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Filtered cohort saved to {output_path}")
    
    # Report zero variance status
    if skipped:
        logger.error(f"Zero-variance detected in: {zero_var_cols}. Correlation analysis should be skipped.")
        # Create a flag file to indicate zero variance was detected
        flag_path = PROCESSED_DATA_DIR / "zero_variance_flag.txt"
        with open(flag_path, 'w') as f:
            f.write(f"Zero-variance detected in columns: {zero_var_cols}\n")
            f.write("Correlation analysis skipped.\n")
        logger.info(f"Zero variance flag created at {flag_path}")
    else:
        logger.info("No zero-variance detected. Ready for correlation analysis.")
    
    return filtered_df, skipped, zero_var_cols

if __name__ == "__main__":
    main()