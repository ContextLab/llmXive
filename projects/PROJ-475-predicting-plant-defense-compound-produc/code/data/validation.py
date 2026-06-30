"""
Data validation module for the plant defense compound prediction pipeline.

Handles loading, merging, listwise deletion, and integrity validation of
genomic, environmental, and compound datasets.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd
import numpy as np

from utils.logging import get_module_logger
from utils.io import DiskSpaceError, check_disk_space
from config import get_config

# Initialize logger for this module
logger = get_module_logger(__name__)

# Required columns for validation
REQUIRED_COLUMNS = ['population_id', 'env_id', 'compound_id']

# Retention threshold (SC-001)
RETENTION_THRESHOLD = 0.80

def load_json_data(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON data file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Parsed JSON data as a dictionary.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    logger.info(f"Loading JSON data from {file_path}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Successfully loaded {len(data) if isinstance(data, list) else 'data'} from {file_path}")
    return data

def merge_datasets(genomic_df: pd.DataFrame, env_df: pd.DataFrame, compound_df: pd.DataFrame) -> pd.DataFrame:
    """Merge genomic, environmental, and compound datasets.
    
    Performs an inner join on all three datasets based on their respective IDs.
    
    Args:
        genomic_df: DataFrame containing genomic data.
        env_df: DataFrame containing environmental data.
        compound_df: DataFrame containing compound data.
        
    Returns:
        Merged DataFrame with all matching records.
    """
    logger.info("Merging datasets")
    
    # Merge genomic and environmental data
    merged = pd.merge(
        genomic_df,
        env_df,
        left_on='population_id',
        right_on='population_id',
        how='inner'
    )
    
    # Merge with compound data
    merged = pd.merge(
        merged,
        compound_df,
        left_on='compound_id',
        right_on='compound_id',
        how='inner'
    )
    
    logger.info(f"Merged dataset has {len(merged)} rows")
    return merged

def perform_listwise_deletion(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Perform listwise deletion for missing modalities (FR-003).
    
    Removes any row that has missing values in the required columns.
    Tracks exclusion counts for reporting.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Tuple of (cleaned DataFrame, exclusion counts dictionary).
    """
    logger.info("Performing listwise deletion for missing modalities")
    
    original_count = len(df)
    exclusion_counts = {
        'population_id_missing': 0,
        'env_id_missing': 0,
        'compound_id_missing': 0,
        'total_excluded': 0
    }
    
    # Check for missing values in required columns
    for col in REQUIRED_COLUMNS:
        missing_mask = df[col].isna()
        count = missing_mask.sum()
        exclusion_counts[f'{col}_missing'] = int(count)
        
        if count > 0:
            logger.warning(f"Found {count} missing values in column '{col}'")
    
    # Perform listwise deletion
    cleaned_df = df.dropna(subset=REQUIRED_COLUMNS)
    
    exclusion_counts['total_excluded'] = original_count - len(cleaned_df)
    
    logger.info(f"Listwise deletion excluded {exclusion_counts['total_excluded']} rows")
    logger.info(f"Remaining rows: {len(cleaned_df)}")
    
    return cleaned_df, exclusion_counts

def validate_data_integrity(df: pd.DataFrame) -> bool:
    """Validate data integrity after cleaning.
    
    Checks that all required columns exist and have no null values.
    
    Args:
        df: DataFrame to validate.
        
    Returns:
        True if validation passes, False otherwise.
    """
    logger.info("Validating data integrity")
    
    # Check required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Check for null values in required columns
    for col in REQUIRED_COLUMNS:
        if df[col].isna().any():
            logger.error(f"Found null values in required column '{col}'")
            return False
    
    logger.info("Data integrity validation passed")
    return True

def calculate_retention_percentage(original_count: int, final_count: int) -> float:
    """Calculate the retention percentage after data cleaning.
    
    Args:
        original_count: Number of rows before cleaning.
        final_count: Number of rows after cleaning.
        
    Returns:
        Retention percentage as a float (0.0 to 1.0).
    """
    if original_count == 0:
        return 0.0
    return final_count / original_count

def run_validation_pipeline(
    genomic_path: Path,
    env_path: Path,
    compound_path: Path,
    output_path: Path
) -> pd.DataFrame:
    """Run the complete validation pipeline.
    
    This function orchestrates the loading, merging, listwise deletion,
    and validation of the datasets. It also calculates and reports
    the retention percentage (SC-001) and logs exclusion warnings.
    
    Args:
        genomic_path: Path to genomic data JSON file.
        env_path: Path to environmental data JSON file.
        compound_path: Path to compound data JSON file.
        output_path: Path to save the cleaned DataFrame.
        
    Returns:
        Cleaned and validated DataFrame.
        
    Raises:
        SystemExit: If retention percentage is below threshold (SC-001).
        FileNotFoundError: If any input file is missing.
    """
    logger.info("Starting validation pipeline")
    
    # Load datasets
    genomic_data = load_json_data(genomic_path)
    env_data = load_json_data(env_path)
    compound_data = load_json_data(compound_path)
    
    # Convert to DataFrames
    genomic_df = pd.DataFrame(genomic_data)
    env_df = pd.DataFrame(env_data)
    compound_df = pd.DataFrame(compound_data)
    
    original_count = min(len(genomic_df), len(env_df), len(compound_df))
    logger.info(f"Original dataset sizes - Genomic: {len(genomic_df)}, Env: {len(env_df)}, Compound: {len(compound_df)}")
    
    # Merge datasets
    merged_df = merge_datasets(genomic_df, env_df, compound_df)
    
    # Perform listwise deletion and get exclusion counts
    cleaned_df, exclusion_counts = perform_listwise_deletion(merged_df)
    
    # Calculate retention percentage
    retention = calculate_retention_percentage(original_count, len(cleaned_df))
    retention_pct = retention * 100
    
    # Report retention percentage (SC-001)
    logger.info(f"Retention percentage: {retention_pct:.2f}% ({len(cleaned_df)}/{original_count} rows)")
    
    # Log exclusion warnings
    if exclusion_counts['total_excluded'] > 0:
        logger.warning(f"Total rows excluded due to missing data: {exclusion_counts['total_excluded']}")
        for col, count in exclusion_counts.items():
            if col != 'total_excluded' and count > 0:
                logger.warning(f"  - {col}: {count} rows")
    
    # Check retention threshold (SC-001)
    if retention < RETENTION_THRESHOLD:
        error_msg = f"E-DATA-INSUFFICIENT: Retention percentage ({retention_pct:.2f}%) is below threshold ({RETENTION_THRESHOLD * 100}%)"
        logger.error(error_msg)
        raise SystemExit("E-DATA-INSUFFICIENT")
    
    # Validate data integrity
    if not validate_data_integrity(cleaned_df):
        error_msg = "E-DATA-INVALID: Data integrity validation failed"
        logger.error(error_msg)
        raise SystemExit("E-DATA-INVALID")
    
    # Save cleaned data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")
    
    # Check disk space after writing
    estimated_size = output_path.stat().st_size if output_path.exists() else 0
    check_disk_space(estimated_size)
    
    logger.info("Validation pipeline completed successfully")
    return cleaned_df

def main():
    """Main entry point for the validation script."""
    logger.info("Running validation script")
    
    # Load configuration
    config = get_config()
    
    # Define paths
    base_path = Path(config.get('paths', {}).get('data_raw', 'data/raw'))
    output_path = Path(config.get('paths', {}).get('data_processed', 'data/processed')) / 'validated.csv'
    
    genomic_path = base_path / 'genomic_vcf.json'
    env_path = base_path / 'env_data.json'
    compound_path = base_path / 'compound_data.json'
    
    # Run validation pipeline
    try:
        cleaned_df = run_validation_pipeline(
            genomic_path,
            env_path,
            compound_path,
            output_path
        )
        logger.info(f"Validation complete. Retained {len(cleaned_df)} rows.")
    except SystemExit as e:
        logger.error(f"Validation failed: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        raise

if __name__ == "__main__":
    main()