"""
Merge preprocessed GRACE-FO and NOAA AR data into a single CSV.

This script:
1. Loads preprocessed monthly data from code/02_preprocessing.py outputs.
2. Merges them on date.
3. Validates completeness (>= 90% of expected months).
4. Ensures no NaN values in primary columns.
5. Validates against contracts/dataset.schema.yaml.
6. Saves to data/processed/merged_monthly.csv.
"""
import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Project paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
OUTPUT_FILE = PROCESSED_DIR / "merged_monthly.csv"
SCHEMA_FILE = CONTRACTS_DIR / "dataset.schema.yaml"

# Expected columns per data-model.md and dataset.schema.yaml
EXPECTED_COLUMNS = [
    "date",
    "grace_anomaly",
    "ar_iwt_mean",
    "ar_iwt_std",
    "ar_event_count"
]

def load_preprocessed_grace():
    """Load preprocessed GRACE-FO monthly data."""
    grace_path = PROCESSED_DIR / "grace_monthly_processed.csv"
    if not grace_path.exists():
        # Fallback: look in raw if preprocessing output not yet in processed
        grace_path = RAW_DIR / "grace-fo" / "grace_monthly_processed.csv"
    
    if not grace_path.exists():
        raise FileNotFoundError(f"Preprocessed GRACE data not found at {grace_path}")
    
    logger.info(f"Loading GRACE data from {grace_path}")
    df = pd.read_csv(grace_path)
    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])
    return df

def load_preprocessed_ar():
    """Load preprocessed NOAA AR monthly data."""
    ar_path = PROCESSED_DIR / "ar_monthly_processed.csv"
    if not ar_path.exists():
        # Fallback: look in raw
        ar_path = RAW_DIR / "noaa-ar" / "ar_monthly_processed.csv"
    
    if not ar_path.exists():
        raise FileNotFoundError(f"Preprocessed AR data not found at {ar_path}")
    
    logger.info(f"Loading AR data from {ar_path}")
    df = pd.read_csv(ar_path)
    df['date'] = pd.to_datetime(df['date'])
    return df

def merge_datasets(grace_df, ar_df):
    """Merge GRACE and AR datasets on date."""
    logger.info("Merging GRACE and AR datasets")
    
    # Select relevant columns
    grace_cols = ['date', 'grace_anomaly']
    ar_cols = ['date', 'ar_iwt_mean', 'ar_iwt_std', 'ar_event_count']
    
    grace_subset = grace_df[grace_cols]
    ar_subset = ar_df[ar_cols]
    
    # Outer merge to see all available data, then filter
    merged = pd.merge(grace_subset, ar_subset, on='date', how='inner')
    
    # Sort by date
    merged = merged.sort_values('date').reset_index(drop=True)
    
    return merged

def validate_completeness(df):
    """Validate completeness (>= 90% of expected months)."""
    if df.empty:
        logger.warning("Merged dataset is empty!")
        return False
    
    # Expected months: from first to last date in data
    # Assuming ~10 years of data (120 months) as a baseline for 90% check
    # More robust: check against actual available months in source data
    total_rows = len(df)
    grace_source = load_preprocessed_grace()
    ar_source = load_preprocessed_ar()
    
    grace_months = grace_source['date'].nunique()
    ar_months = ar_source['date'].nunique()
    expected_months = min(grace_months, ar_months)
    
    completeness = total_rows / expected_months if expected_months > 0 else 0
    
    logger.info(f"Data completeness: {completeness:.2%} ({total_rows}/{expected_months} months)")
    
    if completeness < 0.90:
        logger.warning(f"Completeness {completeness:.2%} is below 90% threshold!")
        return False
    
    return True

def validate_no_nans(df):
    """Ensure no NaN values in primary columns."""
    primary_cols = ['grace_anomaly', 'ar_iwt_mean', 'ar_event_count']
    missing = df[primary_cols].isna().sum()
    
    if missing.any():
        logger.warning(f"NaN values found in primary columns:\n{missing}")
        return False
    
    logger.info("No NaN values in primary columns.")
    return True

def load_schema():
    """Load dataset schema from YAML."""
    if not SCHEMA_FILE.exists():
        logger.warning(f"Schema file not found at {SCHEMA_FILE}, skipping validation")
        return None
    
    with open(SCHEMA_FILE, 'r') as f:
        schema = yaml.safe_load(f)
    return schema

def validate_against_schema(df, schema):
    """Validate dataframe against schema."""
    if schema is None:
        return True
    
    required_columns = schema.get('required_columns', [])
    column_types = schema.get('column_types', {})
    
    # Check required columns
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Check column types (basic check)
    for col, expected_type in column_types.items():
        if col in df.columns:
            if expected_type == 'numeric':
                if not pd.api.types.is_numeric_dtype(df[col]):
                    logger.warning(f"Column {col} is not numeric")
            elif expected_type == 'datetime':
                if not pd.api.types.is_datetime64_any_dtype(df[col]):
                    logger.warning(f"Column {col} is not datetime")
    
    logger.info("Schema validation passed.")
    return True

def main():
    """Main entry point for merge output script."""
    logger.info("Starting merge output process")
    
    try:
        # Load preprocessed data
        grace_df = load_preprocessed_grace()
        ar_df = load_preprocessed_ar()
        
        # Merge datasets
        merged_df = merge_datasets(grace_df, ar_df)
        
        if merged_df.empty:
            logger.error("Merged dataset is empty after merge!")
            sys.exit(1)
        
        # Validate completeness
        completeness_ok = validate_completeness(merged_df)
        
        # Validate no NaNs
        no_nans_ok = validate_no_nans(merged_df)
        
        # Load and validate schema
        schema = load_schema()
        schema_ok = validate_against_schema(merged_df, schema) if schema else True
        
        # Ensure output directory exists
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Save merged CSV
        merged_df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Merged dataset saved to {OUTPUT_FILE}")
        
        # Final validation summary
        if completeness_ok and no_nans_ok and schema_ok:
            logger.info("All validations passed. Merge complete.")
            sys.exit(0)
        else:
            logger.warning("Some validations failed. Check logs for details.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during merge process: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()