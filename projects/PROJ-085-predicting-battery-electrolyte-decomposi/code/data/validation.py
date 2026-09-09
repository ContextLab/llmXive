import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from config import get_project_root, get_processed_dir, get_validation_dir
from utils.logging_config import get_logger, log_feature_extraction_error

# Ensure parent modules are in path if running as script
if 'code' not in sys.path:
    code_root = get_project_root()
    if code_root:
        sys.path.insert(0, str(code_root))

logger = get_logger(__name__)

def validate_feature_matrix(df: pd.DataFrame, feature_columns: List[str]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validates that the feature matrix has no missing values in the specified feature columns.
    
    Args:
        df: The pandas DataFrame containing the feature matrix.
        feature_columns: List of column names that must be non-null.
        
    Returns:
        Tuple containing:
        - is_valid: Boolean indicating if validation passed.
        - missing_columns: List of column names with missing values (empty if valid).
        - summary: Dict with counts of missing values per column.
    """
    if df is None or df.empty:
        logger.error("Feature matrix is empty or None.")
        return False, ["(empty)"], {}

    missing_info = {}
    missing_columns = []
    
    for col in feature_columns:
        if col not in df.columns:
            logger.error(f"Required feature column '{col}' not found in DataFrame. Columns: {list(df.columns)}")
            missing_columns.append(col)
            missing_info[col] = "Missing column"
            continue
        
        null_count = df[col].isnull().sum()
        na_count = df[col].isna().sum()
        total_missing = null_count + na_count
        
        if total_missing > 0:
            missing_columns.append(col)
            missing_info[col] = int(total_missing)
            logger.warning(f"Column '{col}' has {total_missing} missing values.")
        else:
            missing_info[col] = 0

    is_valid = len(missing_columns) == 0
    
    if not is_valid:
        logger.error(f"Validation failed. Missing values found in columns: {missing_columns}")
    else:
        logger.info("Validation passed: No missing values in feature matrix.")
        
    return is_valid, missing_columns, missing_info

def clean_or_drop_missing(df: pd.DataFrame, feature_columns: List[str], 
                          mode: str = "drop") -> Tuple[pd.DataFrame, int]:
    """
    Handles missing values in the feature matrix.
    
    Args:
        df: Input DataFrame.
        feature_columns: List of feature columns to check.
        mode: Strategy to handle missing values. 
              "drop": Drop rows with any missing values in feature columns.
              "error": Raise an error if missing values are found (does not modify df).
              
    Returns:
        Tuple of (cleaned_df, dropped_count).
        If mode is "error" and missing values exist, raises ValueError.
    """
    if mode not in ["drop", "error"]:
        raise ValueError(f"Invalid mode '{mode}'. Use 'drop' or 'error'.")

    is_valid, missing_cols, _ = validate_feature_matrix(df, feature_columns)
    
    if not is_valid:
        if mode == "error":
            raise ValueError(f"Missing values found in feature matrix: {missing_cols}. "
                             f"Validation failed. Please fix data source or enable 'drop' mode.")
        
        initial_len = len(df)
        # Filter out rows where any of the feature columns are null
        mask = df[feature_columns].notna().all(axis=1)
        df_clean = df[mask].reset_index(drop=True)
        dropped_count = initial_len - len(df_clean)
        
        if dropped_count > 0:
            logger.warning(f"Dropped {dropped_count} rows ({100*dropped_count/initial_len:.2f}%) due to missing values in features: {missing_cols}.")
        else:
            # Should not happen if is_valid is False, but safety check
            logger.warning("Missing values detected but no rows dropped? Check logic.")
            
        return df_clean, dropped_count
    
    return df, 0

def run_validation_pipeline() -> bool:
    """
    Main entry point to run the validation pipeline on processed features.
    Reads data from data/processed/electrolyte_features.csv, validates it,
    and either cleans it or raises an error depending on configuration.
    
    Returns:
        True if validation passed (or cleanup successful), False otherwise.
    """
    processed_dir = get_processed_dir()
    if not processed_dir:
        logger.error("Processed directory not configured.")
        return False
        
    input_path = processed_dir / "electrolyte_features.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return False
        
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        return False
        
    # Determine feature columns (exclude known non-feature columns)
    exclude_cols = ['molecule_id', 'potential_v', 'decomp_energy', 'bin_label']
    feature_columns = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_columns:
        logger.error("No feature columns detected in the dataset.")
        return False
        
    logger.info(f"Validating {len(feature_columns)} feature columns.")
    
    is_valid, missing_cols, missing_info = validate_feature_matrix(df, feature_columns)
    
    if not is_valid:
        # Attempt to clean by dropping rows with missing values
        logger.info("Attempting to clean data by dropping rows with missing values...")
        try:
            df_clean, dropped = clean_or_drop_missing(df, feature_columns, mode="drop")
            
            if len(df_clean) == 0:
                logger.critical("All rows dropped due to missing values. Cannot proceed.")
                return False
                
            # Save the cleaned data back to the processed directory
            output_path = processed_dir / "electrolyte_features_cleaned.csv"
            df_clean.to_csv(output_path, index=False)
            logger.info(f"Saved cleaned dataset to {output_path} ({len(df_clean)} rows).")
            
            # Update the main file to point to the cleaned version or overwrite?
            # Per task T017, we ensure the matrix has no missing values before output.
            # We will overwrite the original to ensure downstream tasks see clean data.
            df_clean.to_csv(input_path, index=False)
            logger.info(f"Overwritten {input_path} with cleaned data.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clean data: {e}")
            return False
    else:
        logger.info("Data validation passed. No cleaning required.")
        return True

if __name__ == "__main__":
    success = run_validation_pipeline()
    sys.exit(0 if success else 1)
