import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np

from code.src.utils.config import get_processed_data_dir, get_logs_dir, get_project_root
from code.src.utils.validation import load_schema, validate_dataframe_against_schema

# Initialize logger for this module
logger = logging.getLogger(__name__)

def check_zero_variance(df: pd.DataFrame, columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if any of the specified columns in the DataFrame have zero variance (constant values).
    
    Zero variance in key variables (e.g., diversity scores or cognitive scores) makes
    correlation analysis impossible and can cause statistical errors.
    
    Args:
        df: The DataFrame to check.
        columns: List of column names to check for zero variance.
        
    Returns:
        Tuple of (has_zero_variance, list_of_zero_variance_columns)
    """
    zero_variance_cols = []
    
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column '{col}' not found in DataFrame, skipping variance check.")
            continue
        
        # Check if column is numeric
        if not np.issubdtype(df[col].dtype, np.number):
            logger.info(f"Column '{col}' is not numeric, skipping variance check.")
            continue
        
        # Calculate variance (ddof=1 for sample variance)
        variance = df[col].var()
        
        if pd.isna(variance) or variance == 0.0:
            zero_variance_cols.append(col)
            logger.warning(f"Column '{col}' has zero variance (constant value). "
                         f"Correlation analysis will be skipped for this variable.")
    
    has_zero_variance = len(zero_variance_cols) > 0
    return has_zero_variance, zero_variance_cols

def filter_cohort(
    df: pd.DataFrame,
    min_age: int = 65,
    required_columns: Optional[List[str]] = None,
    check_variance: bool = True,
    variance_columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, dict]:
    """
    Filter the cohort based on age, non-null values, and optional zero-variance checks.
    
    This function implements the core filtering logic for User Story 1:
    1. Filter for age >= min_age
    2. Remove rows with missing values in required columns (listwise deletion)
    3. Optionally check for zero-variance in key analysis columns
    
    Args:
        df: Input DataFrame with cohort data.
        min_age: Minimum age threshold (default 65).
        required_columns: List of columns that must not be null (default: schema-defined covariates).
        check_variance: Whether to check for zero variance in key columns.
        variance_columns: List of columns to check for zero variance (default: diversity and cognitive scores).
        
    Returns:
        Tuple of (filtered DataFrame, status dictionary with counts and flags)
    """
    if required_columns is None:
        # Required columns per spec: age, sex, BMI, dietary_fiber, antibiotic_use
        # Plus the key analysis variables
        required_columns = ['age', 'sex', 'bmi', 'dietary_fiber', 'antibiotic_use',
                          'shannon_diversity', 'cognitive_flexibility_score']
    
    if variance_columns is None:
        variance_columns = ['shannon_diversity', 'simpson_diversity', 
                          'chao1', 'cognitive_flexibility_score']
    
    initial_count = len(df)
    logger.info(f"Starting cohort filtering. Initial rows: {initial_count}")
    
    # Step 1: Age filtering
    df_filtered = df[df['age'] >= min_age].copy()
    age_filtered_count = len(df_filtered)
    logger.info(f"After age filter (>= {min_age}): {age_filtered_count} rows "
               f"(dropped {initial_count - age_filtered_count})")
    
    # Step 2: Listwise deletion for missing required columns
    df_filtered = df_filtered.dropna(subset=required_columns)
    after_null_count = len(df_filtered)
    logger.info(f"After listwise deletion for required columns: {after_null_count} rows "
               f"(dropped {age_filtered_count - after_null_count})")
    
    # Step 3: Zero-variance check (edge case handling)
    status = {
        'initial_rows': initial_count,
        'after_age_filter': age_filtered_count,
        'after_null_removal': after_null_count,
        'zero_variance_detected': False,
        'zero_variance_columns': [],
        'final_rows': after_null_count
    }
    
    if check_variance and after_null_count > 0:
        has_zero_var, zero_var_cols = check_zero_variance(df_filtered, variance_columns)
        status['zero_variance_detected'] = has_zero_var
        status['zero_variance_columns'] = zero_var_cols
        
        if has_zero_var:
            logger.warning(f"Zero variance detected in columns: {zero_var_cols}. "
                         f"Correlation analysis should be skipped or handled specially.")
    
    logger.info(f"Cohort filtering complete. Final rows: {after_null_count}")
    return df_filtered, status

def main():
    """
    Main entry point for the filtering script.
    Reads the ingested cohort, applies filters, and saves the result.
    """
    project_root = get_project_root()
    processed_dir = get_processed_data_dir()
    logs_dir = get_logs_dir()
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup logging for this script
    log_file = logs_dir / "filtering.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    
    # Load schema for validation
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    schema = load_schema(schema_path)
    
    # Input file path
    input_path = project_root / "data" / "raw" / "synthetic_data.csv"
    output_path = processed_dir / "filtered_cohort.csv"
    
    logger.info(f"Loading data from {input_path}")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Apply filtering
    filtered_df, status = filter_cohort(
        df,
        min_age=65,
        required_columns=['age', 'sex', 'bmi', 'dietary_fiber', 'antibiotic_use',
                        'shannon_diversity', 'cognitive_flexibility_score'],
        check_variance=True,
        variance_columns=['shannon_diversity', 'simpson_diversity',
                        'chao1', 'cognitive_flexibility_score']
    )
    
    # Validate against schema
    logger.info("Validating filtered data against schema...")
    try:
        validate_dataframe_against_schema(filtered_df, schema)
        logger.info("Schema validation passed.")
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        sys.exit(1)
    
    # Save results
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Filtered cohort saved to {output_path}")
    
    # Log status summary
    logger.info(f"Filtering summary: {status}")
    
    # Print summary to stdout
    print(f"Filtering complete. Final cohort size: {status['final_rows']}")
    print(f"Zero variance detected: {status['zero_variance_detected']}")
    if status['zero_variance_columns']:
        print(f"Affected columns: {', '.join(status['zero_variance_columns'])}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())