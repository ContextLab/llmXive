"""
Validation utilities for the Plant Defense Compound Prediction Pipeline.

This module handles data merging, integrity checks, and listwise deletion.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd
import numpy as np

from utils.logging import get_module_logger
from utils.io import check_disk_space, DiskSpaceError

# Configure logger for this module
logger = get_module_logger(__name__)

def load_json_data(
    file_path: str
) -> Dict[str, Any]:
    """
    Load data from a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Loaded data as a dictionary.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    logger.info(f"Loading JSON data from {file_path}")
    with open(path, 'r') as f:
        data = json.load(f)
    logger.info(f"Loaded data with {len(data)} records")
    return data

def merge_datasets(
    genomic_df: pd.DataFrame,
    env_df: pd.DataFrame,
    compound_df: pd.DataFrame,
    on_cols: List[str] = ['population_id', 'env_id', 'compound_id']
) -> pd.DataFrame:
    """
    Merge genomic, environmental, and compound datasets.

    Args:
        genomic_df: Genomic data DataFrame.
        env_df: Environmental data DataFrame.
        compound_df: Compound data DataFrame.
        on_cols: Columns to merge on.

    Returns:
        Merged DataFrame.
    """
    logger.info(f"Merging datasets on columns: {on_cols}")
    
    try:
        merged = genomic_df
        for df in [env_df, compound_df]:
            merged = pd.merge(merged, df, on=on_cols, how='inner')
        
        logger.info(f"Merged dataset has {len(merged)} rows and {len(merged.columns)} columns")
        return merged
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        raise

def perform_listwise_deletion(
    df: pd.DataFrame,
    required_cols: List[str]
) -> Tuple[pd.DataFrame, int, int]:
    """
    Perform listwise deletion for missing modalities.

    Args:
        df: Input DataFrame.
        required_cols: Columns that must not be null.

    Returns:
        Tuple of (cleaned DataFrame, original row count, excluded row count).
    """
    original_count = len(df)
    logger.info(f"Performing listwise deletion on {len(required_cols)} required columns")
    
    # Drop rows with any null in required columns
    cleaned_df = df.dropna(subset=required_cols)
    excluded_count = original_count - len(cleaned_df)
    
    logger.info(f"Listwise deletion: {excluded_count} rows excluded ({excluded_count/original_count*100:.2f}%)")
    
    return cleaned_df, original_count, excluded_count

def validate_data_integrity(
    df: pd.DataFrame,
    required_cols: List[str]
) -> bool:
    """
    Validate data integrity by checking for nulls in required columns.

    Args:
        df: DataFrame to validate.
        required_cols: Columns that must be non-null.

    Returns:
        True if valid, False otherwise.
    """
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Required column '{col}' not found in DataFrame")
            return False
        if df[col].isna().any():
            logger.error(f"Column '{col}' contains null values")
            return False
    
    logger.info("Data integrity validation passed")
    return True

def calculate_retention_percentage(
    original_count: int,
    final_count: int
) -> float:
    """
    Calculate retention percentage after filtering.

    Args:
        original_count: Original number of rows.
        final_count: Final number of rows.

    Returns:
        Retention percentage.
    """
    if original_count == 0:
        return 0.0
    return (len(df) / original_count) * 100

def run_validation_pipeline(
    genomic_path: str = "data/raw/genomic_vcf.json",
    env_path: str = "data/raw/env_data.json",
    compound_path: str = "data/raw/compound_data.json",
    output_path: str = "data/processed/merged_validation.csv"
) -> pd.DataFrame:
    """
    Run the full validation pipeline:
    1. Load JSON data.
    2. Convert to DataFrames.
    3. Merge datasets.
    4. Perform listwise deletion.
    5. Validate integrity.
    6. Calculate retention.

    Args:
        genomic_path: Path to genomic JSON.
        env_path: Path to environmental JSON.
        compound_path: Path to compound JSON.
        output_path: Path to save merged data.

    Returns:
        Validated and merged DataFrame.
    """
    logger.info("Starting validation pipeline.")
    
    # Check disk space
    estimated_size = 100 * 1024 * 1024 # 100MB estimate
    try:
        check_disk_space(estimated_size)
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        raise

    # Load data
    try:
        genomic_data = load_json_data(genomic_path)
        env_data = load_json_data(env_path)
        compound_data = load_json_data(compound_path)
    except FileNotFoundError as e:
        logger.error(f"Missing input file: {e}")
        raise

    # Convert to DataFrames (assuming list of dicts format)
    genomic_df = pd.DataFrame(genomic_data) if isinstance(genomic_data, list) else pd.DataFrame([genomic_data])
    env_df = pd.DataFrame(env_data) if isinstance(env_data, list) else pd.DataFrame([env_data])
    compound_df = pd.DataFrame(compound_data) if isinstance(compound_data, list) else pd.DataFrame([compound_data])

    # Merge datasets
    merged_df = merge_datasets(genomic_df, env_df, compound_df)

    # Define required columns
    required_cols = ['population_id', 'env_id', 'compound_id']

    # Perform listwise deletion
    cleaned_df, original_count, excluded_count = perform_listwise_deletion(merged_df, required_cols)

    # Validate integrity
    is_valid = validate_data_integrity(cleaned_df, required_cols)
    if not is_valid:
        logger.error("Data integrity validation failed")
        raise ValueError("Data integrity validation failed")

    # Calculate retention
    retention = calculate_retention_percentage(original_count, len(cleaned_df))
    logger.info(f"Retention percentage: {retention:.2f}%")

    # Check retention threshold
    if retention < 80.0:
        logger.error(f"Retention {retention:.2f}% is below 80% threshold. Exiting.")
        raise SystemExit("E-DATA-INSUFFICIENT")

    # Save merged data
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(output_file, index=False)
    logger.info(f"Merged validation data saved to {output_path}")

    return cleaned_df

def main():
    """
    Main entry point for validation pipeline.
    """
    from config import get_config
    
    config = get_config()
    paths = config.get('paths', {})
    genomic_path = paths.get('genomic_raw', 'data/raw/genomic_vcf.json')
    env_path = paths.get('env_raw', 'data/raw/env_data.json')
    compound_path = paths.get('compound_raw', 'data/raw/compound_data.json')
    output_path = paths.get('merged_validation', 'data/processed/merged_validation.csv')
    
    try:
        run_validation_pipeline(genomic_path, env_path, compound_path, output_path)
        return True
    except SystemExit as e:
        logger.error(f"Validation pipeline exited: {e}")
        return False
    except Exception as e:
        logger.error(f"Validation pipeline failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
