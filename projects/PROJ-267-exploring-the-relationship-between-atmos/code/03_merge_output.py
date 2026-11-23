"""
Merge preprocessed GRACE-FO and NOAA AR data into a single CSV.

This script performs the final merge step for User Story 1:
1. Loads preprocessed GRACE-FO and NOAA AR data from `data/processed/`.
2. Merges them on the 'date' column (monthly resolution).
3. Validates completeness (>= 90% of expected months).
4. Ensures no NaN values in primary columns.
5. Validates the output against the schema in `contracts/dataset.schema.yaml`.
6. Saves the final merged CSV to `data/processed/merged_monthly.csv`.
"""
import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
OUTPUT_FILE = DATA_PROCESSED_DIR / "merged_monthly.csv"
SCHEMA_FILE = CONTRACTS_DIR / "dataset.schema.yaml"

def load_preprocessed_grace() -> pd.DataFrame:
    """Load preprocessed GRACE-FO data."""
    file_path = DATA_PROCESSED_DIR / "grace_monthly_preprocessed.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Preprocessed GRACE data not found: {file_path}")
    logger.info(f"Loading GRACE-FO data from {file_path}")
    df = pd.read_csv(file_path)
    # Ensure date column is datetime for merging
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df

def load_preprocessed_ar() -> pd.DataFrame:
    """Load preprocessed NOAA AR data."""
    file_path = DATA_PROCESSED_DIR / "ar_monthly_preprocessed.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Preprocessed NOAA AR data not found: {file_path}")
    logger.info(f"Loading NOAA AR data from {file_path}")
    df = pd.read_csv(file_path)
    # Ensure date column is datetime for merging
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df

def merge_datasets(grace_df: pd.DataFrame, ar_df: pd.DataFrame) -> pd.DataFrame:
    """Merge GRACE and AR data on 'date'."""
    logger.info("Merging datasets on 'date' column...")
    # Inner join to keep only months where both datasets have data
    merged_df = pd.merge(grace_df, ar_df, on='date', how='inner')
    logger.info(f"Merged dataset shape: {merged_df.shape}")
    return merged_df

def validate_completeness(df: pd.DataFrame, threshold: float = 0.90) -> bool:
    """
    Validate that the merged dataset has at least `threshold` (default 90%)
    of the expected monthly rows based on the date range.
    """
    if 'date' not in df.columns or len(df) == 0:
        logger.warning("Cannot validate completeness: no date column or empty dataframe.")
        return False

    min_date = df['date'].min()
    max_date = df['date'].max()
    
    # Calculate expected number of months
    total_months = (max_date.year - min_date.year) * 12 + (max_date.month - min_date.month) + 1
    actual_rows = len(df)
    
    completeness = actual_rows / total_months if total_months > 0 else 0.0
    logger.info(f"Date range: {min_date} to {max_date}")
    logger.info(f"Expected months: {total_months}, Actual rows: {actual_rows}")
    logger.info(f"Completeness: {completeness:.2%}")

    if completeness < threshold:
        logger.warning(f"Completeness ({completeness:.2%}) is below threshold ({threshold:.0%}).")
        return False
    
    logger.info(f"Completeness check passed (>= {threshold:.0%}).")
    return True

def validate_no_nans(df: pd.DataFrame, primary_columns: list = None) -> bool:
    """
    Ensure no NaN values in primary columns.
    If primary_columns is None, checks all numeric columns.
    """
    if primary_columns is None:
        # Check all numeric columns
        primary_columns = df.select_dtypes(include=['number']).columns.tolist()
    
    if not primary_columns:
        logger.warning("No numeric columns found to check for NaNs.")
        return True

    nan_counts = df[primary_columns].isna().sum()
    total_nans = nan_counts.sum()
    
    if total_nans > 0:
        logger.error(f"Found {total_nans} NaN values in primary columns:")
        for col, count in nan_counts[nan_counts > 0].items():
            logger.error(f"  - {col}: {count} NaNs")
        return False
    
    logger.info("No NaN values found in primary columns.")
    return True

def load_schema() -> dict:
    """Load the dataset schema from YAML."""
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")
    
    with open(SCHEMA_FILE, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(df: pd.DataFrame, schema: dict) -> bool:
    """
    Validate the dataframe against the loaded schema.
    Checks for required columns and basic type consistency.
    """
    logger.info("Validating against schema...")
    required_columns = schema.get('required_columns', [])
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False
    
    # Check for unexpected columns (optional, based on schema definition)
    allowed_columns = schema.get('allowed_columns', df.columns.tolist())
    extra_columns = [col for col in df.columns if col not in allowed_columns]
    if extra_columns:
        logger.warning(f"Extra columns found (not in allowed list): {extra_columns}")
    
    logger.info("Schema validation passed.")
    return True

def main():
    """Main entry point for the merge output script."""
    try:
        # Ensure output directory exists
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Load data
        grace_df = load_preprocessed_grace()
        ar_df = load_preprocessed_ar()

        # Merge
        merged_df = merge_datasets(grace_df, ar_df)

        if merged_df.empty:
            logger.error("Merged dataset is empty. Check data sources and merge keys.")
            sys.exit(1)

        # Validate completeness
        completeness_ok = validate_completeness(merged_df)
        
        # Validate no NaNs in primary columns (gravity anomaly and AR intensity)
        # Based on typical names, but we can be flexible
        primary_cols = ['gravity_anomaly', 'ar_intensity']
        # If these specific columns don't exist, fall back to all numeric
        if not all(col in merged_df.columns for col in primary_cols):
            primary_cols = None 
        
        no_nans_ok = validate_no_nans(merged_df, primary_columns=primary_cols)

        # Load and validate schema
        schema = load_schema()
        schema_ok = validate_against_schema(merged_df, schema)

        if not (completeness_ok and no_nans_ok and schema_ok):
            logger.error("One or more validation steps failed. Exiting.")
            sys.exit(1)

        # Save output
        merged_df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Successfully saved merged data to {OUTPUT_FILE}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
