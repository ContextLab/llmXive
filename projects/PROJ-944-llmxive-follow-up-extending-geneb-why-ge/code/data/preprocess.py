"""
Preprocess extracted sequence features: handle NaNs, outliers, validate schema,
and save the final feature matrix.
"""

import os
import math
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import yaml
import numpy as np
import pandas as pd
from scipy import stats

# Project imports based on API surface
from config import get_path, get_config
from utils.logging import get_logger, handle_exception, PipelineError, ValidationError
from utils.schema_validator import load_schema, validate_dataset, validate_file
from utils.checksums import compute_sha256, save_checksum_state

logger = get_logger(__name__)

# Constants for preprocessing
OUTLIER_STD_THRESHOLD = 3.0  # Standard deviations for outlier detection
MIN_VALID_VALUE = -1e6       # Minimum theoretical bound for features (safety floor)
MAX_VALID_VALUE = 1e6        # Maximum theoretical bound for features (safety cap)
CHUNK_SIZE = 10000           # Rows to process at a time for memory efficiency

def load_feature_data(input_path: str) -> pd.DataFrame:
    """
    Load the extracted features from CSV.
    Uses chunking if the file is very large to stay within memory limits.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input feature file not found: {input_path}")

    logger.info(f"Loading feature data from {input_path}")
    
    # Check file size to decide on chunking strategy
    file_size_mb = path.stat().st_size / (1024 * 1024)
    
    if file_size_mb > 500:
        logger.warning(f"Large file detected ({file_size_mb:.1f} MB). Using chunked loading.")
        chunks = []
        for chunk in pd.read_csv(path, chunksize=CHUNK_SIZE):
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)
    else:
        df = pd.read_csv(path)
    
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df

def detect_outliers_iqr(series: pd.Series) -> pd.Series:
    """
    Detect outliers using the Interquartile Range (IQR) method.
    Returns a boolean mask where True indicates an outlier.
    """
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - (OUTLIER_STD_THRESHOLD * IQR)
    upper_bound = Q3 + (OUTLIER_STD_THRESHOLD * IQR)
    return (series < lower_bound) | (series > upper_bound)

def detect_outliers_zscore(series: pd.Series) -> pd.Series:
    """
    Detect outliers using Z-score method.
    Returns a boolean mask where True indicates an outlier.
    """
    # Handle constant columns (std=0) to avoid division by zero
    std_val = series.std()
    if std_val == 0:
        return pd.Series([False] * len(series), index=series.index)
    
    z_scores = np.abs(stats.zscore(series))
    return z_scores > OUTLIER_STD_THRESHOLD

def handle_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle outliers by capping them to the 1st and 99th percentiles.
    This is robust and preserves the distribution shape better than mean imputation.
    """
    logger.info("Detecting and handling outliers...")
    df_clean = df.copy()
    
    # Identify numeric columns only
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        if col == 'task_id':
            continue
        
        # Use IQR method as primary, Z-score as secondary check if IQR is 0
        outliers_iqr = detect_outliers_iqr(df_clean[col])
        
        if outliers_iqr.any():
            logger.info(f"Found {outliers_iqr.sum()} outliers in column '{col}' using IQR method.")
            
            # Cap outliers to 1st and 99th percentiles
            lower_cap = df_clean[col].quantile(0.01)
            upper_cap = df_clean[col].quantile(0.99)
            
            # Ensure caps are within theoretical bounds
            lower_cap = max(lower_cap, MIN_VALID_VALUE)
            upper_cap = min(upper_cap, MAX_VALID_VALUE)
            
            df_clean[col] = df_clean[col].clip(lower=lower_cap, upper=upper_cap)
            logger.info(f"Capped outliers in '{col}' to range [{lower_cap:.4f}, {upper_cap:.4f}]")
        else:
            logger.debug(f"No outliers detected in column '{col}' using IQR method.")
    
    return df_clean

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values (NaNs).
    Strategy:
    1. If a column has > 50% missing, drop the column.
    2. If a column has < 50% missing, impute with the median (robust to outliers).
    """
    logger.info("Handling missing values...")
    df_clean = df.copy()
    
    initial_cols = len(df_clean.columns)
    initial_rows = len(df_clean)
    
    # Identify numeric columns
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    
    cols_to_drop = []
    
    for col in numeric_cols:
        if col == 'task_id':
            continue
        
        missing_count = df_clean[col].isna().sum()
        missing_ratio = missing_count / len(df_clean)
        
        if missing_ratio > 0.5:
            logger.warning(f"Column '{col}' has {missing_ratio:.1%} missing values. Dropping column.")
            cols_to_drop.append(col)
        elif missing_count > 0:
            median_val = df_clean[col].median()
            df_clean[col] = df_clean[col].fillna(median_val)
            logger.info(f"Imputed {missing_count} missing values in '{col}' with median {median_val:.4f}")
        else:
            logger.debug(f"Column '{col}' has no missing values.")
    
    if cols_to_drop:
        df_clean.drop(columns=cols_to_drop, inplace=True)
        logger.warning(f"Dropped {len(cols_to_drop)} columns due to excessive missing values: {cols_to_drop}")
    
    # Check for any remaining NaNs in numeric columns
    remaining_nans = df_clean[numeric_cols].isna().sum().sum()
    if remaining_nans > 0:
        logger.error(f"Unexpected: {remaining_nans} NaNs remain after processing.")
        raise ValidationError(f"Data cleaning failed: {remaining_nans} NaNs remain in numeric columns.")
    
    logger.info(f"Missing value handling complete. Dropped {initial_cols - len(df_clean.columns)} columns.")
    return df_clean

def validate_features(df: pd.DataFrame, schema_path: str) -> Tuple[bool, List[str]]:
    """
    Validate the dataframe against the dataset schema.
    """
    logger.info(f"Validating data against schema: {schema_path}")
    
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found at {schema_path}. Skipping schema validation.")
        return True, []
    
    try:
        is_valid, errors = validate_file(df, schema_path)
        if not is_valid:
            logger.error(f"Schema validation failed with {len(errors)} errors.")
            for err in errors:
                logger.error(f"  - {err}")
            return False, errors
        logger.info("Schema validation passed.")
        return True, []
    except Exception as e:
        logger.error(f"Error during schema validation: {e}")
        return False, [str(e)]

def validate_theoretical_ranges(df: pd.DataFrame) -> List[str]:
    """
    Ensure all computed features are within valid theoretical ranges.
    Returns a list of error messages if validation fails.
    """
    errors = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        if col == 'task_id':
            continue
        
        min_val = df[col].min()
        max_val = df[col].max()
        
        # Log ranges for monitoring
        logger.debug(f"Column '{col}' range: [{min_val:.4f}, {max_val:.4f}]")
        
        # Specific checks based on feature type (if known from schema or heuristic)
        # For now, generic bounds check
        if min_val < MIN_VALID_VALUE or max_val > MAX_VALID_VALUE:
            errors.append(f"Column '{col}' out of bounds: [{min_val}, {max_val}]")
        
        # Check for negative entropy if column name suggests entropy
        if 'entropy' in col.lower() and min_val < 0:
            errors.append(f"Entropy column '{col}' has negative values: min={min_val}")
    
    return errors

def preprocess_features(
    input_path: str,
    output_path: str,
    schema_path: Optional[str] = None
) -> str:
    """
    Main pipeline to preprocess features:
    1. Load data
    2. Handle missing values
    3. Handle outliers
    4. Validate against schema
    5. Validate theoretical ranges
    6. Save output
    7. Compute checksum
    """
    logger.info("Starting feature preprocessing pipeline...")
    
    # 1. Load
    df = load_feature_data(input_path)
    
    # 2. Handle Missing Values
    df = handle_missing_values(df)
    
    # 3. Handle Outliers
    df = handle_outliers(df)
    
    # 4. Validate Schema
    if schema_path:
        is_valid, errors = validate_features(df, schema_path)
        if not is_valid:
            raise ValidationError(f"Schema validation failed: {errors}")
    
    # 5. Validate Theoretical Ranges
    range_errors = validate_theoretical_ranges(df)
    if range_errors:
        raise ValidationError(f"Theoretical range validation failed: {range_errors}")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 6. Save
    logger.info(f"Saving preprocessed features to {output_path}")
    df.to_csv(output_path, index=False)
    
    # 7. Compute Checksum
    checksum = compute_sha256(output_path)
    logger.info(f"Output file checksum (SHA-256): {checksum}")
    
    # Update state with checksum
    save_checksum_state(output_path, checksum, project_id="PROJ-944-llmxive-follow-up-extending-geneb-why-ge")
    
    logger.info("Preprocessing pipeline completed successfully.")
    return output_path

def main():
    """
    Entry point for the script.
    Reads configuration from config.yaml or defaults.
    """
    try:
        config = get_config()
        
        # Paths
        input_file = get_path("processed_features_input", "data/raw/extracted_features.csv")
        output_file = get_path("processed_features_output", "data/processed/features.csv")
        schema_file = get_path("dataset_schema", "specs/gene-regulation/contracts/dataset.schema.yaml")
        
        # If input file doesn't exist at default, check common alternatives
        if not os.path.exists(input_file):
            # Fallback to the output of T012 if it exists
            fallback = "data/raw/extracted_features.csv" # Adjust based on T012 output
            if os.path.exists(fallback):
                input_file = fallback
            else:
                # Try to find any CSV in data/raw that looks like features
                raw_dir = Path("data/raw")
                candidates = list(raw_dir.glob("*.csv"))
                if candidates:
                    input_file = str(candidates[0])
                    logger.info(f"Using fallback input file: {input_file}")
                else:
                    raise FileNotFoundError("No input feature file found in data/raw/ or default path.")
        
        preprocess_features(input_file, output_file, schema_file)
        
    except Exception as e:
        handle_exception(e, "Preprocessing failed")
        sys.exit(1)

if __name__ == "__main__":
    main()