import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np

from code.src.utils.config import get_logs_dir, get_processed_data_dir, setup_logging

# Setup logging for this module
logger = logging.getLogger(__name__)

# Define the covariates required by the schema (T003)
REQUIRED_COVARIATES = [
    "age",
    "sex",
    "bmi",
    "dietary_fiber_intake",
    "antibiotic_use_history"
]

def check_zero_variance(df: pd.DataFrame, column: str) -> bool:
    """
    Check if a column has zero variance (all values are identical).
    
    Args:
        df: Input DataFrame
        column: Column name to check
        
    Returns:
        True if variance is zero, False otherwise
    """
    if column not in df.columns:
        logger.warning(f"Column {column} not found in DataFrame")
        return False
    
    unique_count = df[column].nunique()
    is_zero_variance = unique_count <= 1
    
    if is_zero_variance:
        logger.warning(f"Column '{column}' has zero variance ({unique_count} unique value(s))")
    
    return is_zero_variance

def filter_cohort(
    df: pd.DataFrame,
    min_age: int = 65,
    required_columns: Optional[List[str]] = None,
    output_path: Optional[str] = None
) -> Tuple[pd.DataFrame, int]:
    """
    Filter the cohort based on age, non-null critical metrics, and listwise deletion
    for missing covariates.
    
    This function implements T011 (age filtering, non-null checks) and T013 
    (listwise deletion for missing covariates).
    
    Args:
        df: Input DataFrame with merged cohort data
        min_age: Minimum age threshold (default 65)
        required_columns: List of columns that must be non-null (default: critical metrics)
        output_path: Optional path to save the filtered DataFrame
        
    Returns:
        Tuple of (filtered DataFrame, number of rows dropped due to missing covariates)
    """
    if required_columns is None:
        required_columns = [
            "shannon_diversity", 
            "cognitive_flexibility_score"
        ]
    
    logger.info(f"Starting cohort filtering. Initial shape: {df.shape}")
    initial_count = len(df)
    
    # Step 1: Filter by age >= min_age (T011)
    logger.info(f"Filtering for age >= {min_age}")
    df_filtered = df[df["age"] >= min_age].copy()
    logger.info(f"After age filter: {len(df_filtered)} rows")
    
    # Step 2: Filter for non-null critical metrics (T011)
    for col in required_columns:
        if col in df_filtered.columns:
            before = len(df_filtered)
            df_filtered = df_filtered.dropna(subset=[col])
            dropped = before - len(df_filtered)
            if dropped > 0:
                logger.info(f"Dropped {dropped} rows due to null values in '{col}'")
        else:
            logger.warning(f"Required column '{col}' not found in DataFrame")
    
    # Step 3: Listwise deletion for missing covariates (T013)
    # Strictly use only the covariates defined in contracts/dataset.schema.yaml
    missing_covariates = [col for col in REQUIRED_COVARIATES if col not in df_filtered.columns]
    if missing_covariates:
        logger.warning(f"Missing required covariates in dataset: {missing_covariates}")
        # If any required covariate is missing entirely, we cannot proceed with listwise deletion
        # for those specific columns, but we proceed with what we have or fail loudly if critical
        logger.error("Cannot perform listwise deletion: Required covariates missing from schema.")
        raise ValueError(f"Missing required covariates defined in schema: {missing_covariates}")
    
    logger.info(f"Applying listwise deletion for covariates: {REQUIRED_COVARIATES}")
    before_covariate_filter = len(df_filtered)
    df_filtered = df_filtered.dropna(subset=REQUIRED_COVARIATES)
    dropped_covariate_rows = before_covariate_filter - len(df_filtered)
    
    logger.info(f"Listwise deletion dropped {dropped_covariate_rows} rows due to missing covariates.")
    logger.info(f"Covariates checked: {REQUIRED_COVARIATES}")
    
    # Step 4: Log the count of dropped rows to logs/filtering.log (T013 Action)
    logs_dir = get_logs_dir()
    log_file = logs_dir / "filtering.log"
    
    # Ensure the logger writes to the file as well
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file) 
               for h in logger.handlers):
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.info(f"=== Filtering Summary ===")
    logger.info(f"Initial rows: {initial_count}")
    logger.info(f"Rows after age filter: {len(df_filtered) + dropped_covariate_rows}") # Approximate intermediate
    logger.info(f"Rows dropped by listwise deletion of covariates: {dropped_covariate_rows}")
    logger.info(f"Final rows: {len(df_filtered)}")
    logger.info(f"Total dropped: {initial_count - len(df_filtered)}")
    logger.info(f"========================")
    
    # Save output if path provided (T011 Action)
    if output_path:
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        df_filtered.to_csv(output_path, index=False)
        logger.info(f"Filtered cohort saved to {output_path}")
    
    return df_filtered, dropped_covariate_rows

def main():
    """
    Main entry point for the filtering script.
    Loads the merged cohort, filters it, and saves the result.
    """
    from code.src.utils.config import get_raw_data_dir, get_processed_data_dir
    
    # Setup logging
    setup_logging()
    
    # Define paths
    input_path = get_raw_data_dir() / "synthetic_data.csv"
    output_path = get_processed_data_dir() / "filtered_cohort.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    # Perform filtering
    try:
        filtered_df, dropped_count = filter_cohort(df, output_path=str(output_path))
        logger.info(f"Filtering complete. Dropped {dropped_count} rows due to missing covariates.")
    except ValueError as e:
        logger.error(f"Filtering failed: {e}")
        sys.exit(1)
    
    logger.info("Pipeline step 'filtering' completed successfully.")

if __name__ == "__main__":
    main()