import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Import logging utilities from the shared module
from logging_config import (
    setup_logging,
    get_module_logger,
    log_operation_start,
    log_operation_complete,
    log_data_filter_step,
    log_skipped_row,
    log_zero_variance_field
)

class DataFetchError(Exception):
    """Custom exception for data fetching/loading failures."""
    pass

def load_raw_data(data_path: str) -> pd.DataFrame:
    """
    Loads the raw CSV data.
    
    Args:
        data_path: Path to the raw CSV file.
        
    Returns:
        Pandas DataFrame.
        
    Raises:
        DataFetchError: If the data file is missing or unreadable.
    """
    logger = get_module_logger(__name__)
    log_operation_start(logger, "Load Raw Data")
    
    if not os.path.exists(data_path):
        error_msg = f"Raw data file not found: {data_path}"
        logger.error(error_msg)
        raise DataFetchError(error_msg)
        
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} rows from {data_path}")
    except Exception as e:
        error_msg = f"Failed to read CSV file {data_path}: {str(e)}"
        logger.error(error_msg)
        raise DataFetchError(error_msg)
    
    log_operation_complete(logger, "Load Raw Data")
    return df

def validate_grouping_variables(df: pd.DataFrame, grouping_vars: list) -> dict:
    """
    Validates grouping variables for variance and cardinality.
    
    Args:
        df: The dataframe containing the data.
        grouping_vars: List of column names to validate as grouping factors.
        
    Returns:
        Dictionary with validation status for each factor.
    """
    logger = get_module_logger(__name__)
    log_operation_start(logger, "Validate Grouping Variables")
    
    validation_results = {}
    
    for var in grouping_vars:
        if var not in df.columns:
            validation_results[var] = {"status": "missing", "count": 0, "reason": f"Column '{var}' not found"}
            log_skipped_row(logger, -1, f"Grouping variable '{var}' missing from data")
            continue
        
        unique_count = df[var].nunique()
        
        # Check for single level (zero variance)
        if unique_count <= 1:
            validation_results[var] = {
                "status": "single_level", 
                "count": unique_count, 
                "reason": "Only one unique level found"
            }
            log_zero_variance_field(logger, var, unique_count)
        else:
            validation_results[var] = {
                "status": "valid", 
                "count": unique_count
            }
            logger.info(f"Grouping variable '{var}' is valid with {unique_count} levels.")
    
    log_operation_complete(logger, "Validate Grouping Variables")
    return validation_results

def save_grouping_validation(validation_results: dict, output_path: str):
    """
    Saves the grouping validation results to a JSON file.
    
    Args:
        validation_results: Dictionary of validation results.
        output_path: Path to save the JSON file.
    """
    logger = get_module_logger(__name__)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    logger.info(f"Grouping validation saved to {output_path}")

def save_cleaned_data(df: pd.DataFrame, output_path: str):
    """
    Saves the cleaned dataframe to a CSV file.
    
    Args:
        df: The cleaned dataframe.
        output_path: Path to save the CSV file.
    """
    logger = get_module_logger(__name__)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path} ({len(df)} rows)")

def main():
    """
    Main execution flow for preprocessing:
    1. Load raw data.
    2. Filter rows with missing critical columns (year, effect_size, sample_size).
    3. Validate grouping variables (field, original_study_id).
    4. Save cleaned data and grouping validation report.
    """
    logger = setup_logging()
    logger.info("Starting Preprocessing Pipeline")
    
    # Paths
    raw_data_path = "data/raw/data.csv"
    cleaned_data_path = "data/derived/cleaned_data.csv"
    validation_path = "data/derived/grouping_validation.json"
    
    # Load data
    try:
        df = load_raw_data(raw_data_path)
    except DataFetchError as e:
        logger.error(str(e))
        sys.exit(1)
    
    rows_before = len(df)
    
    # Filter rows with missing critical columns
    # FR-008: Filter rows with missing year, effect_size, or sample_size
    critical_cols = ['year', 'effect_size', 'sample_size']
    
    # Ensure critical columns exist
    missing_cols = [col for col in critical_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing expected columns: {missing_cols}. Proceeding with available data.")
    
    # Identify rows with missing values in critical columns
    # We check only columns that exist
    available_critical_cols = [col for col in critical_cols if col in df.columns]
    
    if available_critical_cols:
        missing_mask = df[available_critical_cols].isnull().any(axis=1)
        
        if missing_mask.any():
            logger.warning(f"Found {missing_mask.sum()} rows with missing critical data.")
            # Log skipped rows (FR-014)
            for idx in df.index[missing_mask]:
                row = df.loc[idx]
                reasons = []
                for col in available_critical_cols:
                    if pd.isna(row[col]):
                        reasons.append(f"NaN in {col}")
                reason_str = ", ".join(reasons)
                log_skipped_row(logger, idx, reason_str)
            
            df_cleaned = df.dropna(subset=available_critical_cols)
        else:
            df_cleaned = df.copy()
    else:
        logger.warning("No critical columns found to filter on. Keeping all rows.")
        df_cleaned = df.copy()
    
    rows_after = len(df_cleaned)
    log_data_filter_step(
        logger, 
        raw_data_path, 
        cleaned_data_path, 
        rows_before, 
        rows_after, 
        "Removed rows with missing year, effect_size, or sample_size"
    )
    
    # Validate grouping variables
    grouping_vars = ['field', 'original_study_id']
    validation_results = validate_grouping_variables(df_cleaned, grouping_vars)
    
    # Save outputs
    save_grouping_validation(validation_results, validation_path)
    save_cleaned_data(df_cleaned, cleaned_data_path)
    
    logger.info("Preprocessing Pipeline Completed Successfully")

if __name__ == "__main__":
    main()
