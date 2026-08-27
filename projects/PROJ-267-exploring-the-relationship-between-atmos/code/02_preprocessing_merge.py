"""
Merge and validation script for Atmospheric River Gravity Correlation project.

Merges processed GRACE-FO and NOAA AR data, validates against schema,
and outputs the final merged dataset.
"""
import os
import sys
import logging
import json
import pandas as pd
from pathlib import Path
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_GRACE_PATH = PROJECT_ROOT / "data" / "processed" / "grace_processed_monthly.csv"
PROCESSED_NOAA_PATH = PROJECT_ROOT / "data" / "processed" / "noaa_processed_monthly.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "merged_monthly.csv"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

def load_processed_grace():
    """Load preprocessed GRACE-FO data."""
    if not PROCESSED_GRACE_PATH.exists():
        raise FileNotFoundError(
            f"GRACE processed data not found at {PROCESSED_GRACE_PATH}. "
            "Run 02_preprocessing_grace.py first."
        )
    df = pd.read_csv(PROCESSED_GRACE_PATH)
    logger.info(f"Loaded GRACE data: {len(df)} rows")
    return df

def load_processed_noaa():
    """Load preprocessed NOAA AR data."""
    if not PROCESSED_NOAA_PATH.exists():
        raise FileNotFoundError(
            f"NOAA processed data not found at {PROCESSED_NOAA_PATH}. "
            "Run 02_preprocessing_noaa.py first."
        )
    df = pd.read_csv(PROCESSED_NOAA_PATH)
    logger.info(f"Loaded NOAA data: {len(df)} rows")
    return df

def merge_datasets(grace_df, noaa_df):
    """Merge GRACE and NOAA data on date."""
    # Ensure date columns are datetime
    grace_df['date'] = pd.to_datetime(grace_df['date'])
    noaa_df['date'] = pd.to_datetime(noaa_df['date'])
    
    # Merge on date
    merged = pd.merge(
        grace_df,
        noaa_df,
        on='date',
        how='inner',
        suffixes=('_grace', '_noaa')
    )
    
    # Standardize column names for schema compliance
    # Map source columns to canonical schema names
    column_mapping = {}
    if 'anomaly_value' in merged.columns:
        column_mapping['anomaly_value'] = 'gravity_anomaly'
    if 'uncertainty' in merged.columns:
        column_mapping['uncertainty'] = 'uncertainty'
    if 'peak_intensity' in merged.columns:
        column_mapping['peak_intensity'] = 'ar_intensity'
    if 'ar_intensity' in merged.columns and 'peak_intensity' not in merged.columns:
        column_mapping['ar_intensity'] = 'ar_intensity'
    
    merged = merged.rename(columns=column_mapping)
    
    # Select and order columns per schema
    schema_columns = ['date', 'ar_intensity', 'gravity_anomaly', 'uncertainty']
    available_columns = [col for col in schema_columns if col in merged.columns]
    
    if len(available_columns) < len(schema_columns):
        missing = set(schema_columns) - set(available_columns)
        raise ValueError(f"Merge result missing required schema columns: {missing}")
        
    merged = merged[available_columns]
    
    # Ensure date is formatted as ISO 8601 string for schema compliance
    merged['date'] = merged['date'].dt.strftime('%Y-%m-%d')
    
    logger.info(f"Merged dataset: {len(merged)} rows")
    return merged

def load_schema():
    """Load the dataset schema from YAML."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found at {SCHEMA_PATH}. "
            "Run T013 to generate the schema."
        )
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(df, schema):
    """Validate dataframe against JSON schema."""
    errors = []
    
    # Check required columns
    required_cols = schema.get('required', [])
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        raise ValueError(f"Schema validation failed: {errors}")
    
    # Check for NaN values in required columns
    for col in required_cols:
        if df[col].isna().any():
            nan_count = df[col].isna().sum()
            errors.append(f"Column '{col}' contains {nan_count} NaN values")
    
    if errors:
        raise ValueError(f"Data validation failed: {errors}")
    
    # Validate data types
    properties = schema.get('properties', {})
    for col in df.columns:
        if col in properties:
            expected_type = properties[col].get('type')
            if expected_type == 'number':
                if not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(f"Column '{col}' should be numeric")
            elif expected_type == 'string':
                if not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_datetime64_any_dtype(df[col]):
                    errors.append(f"Column '{col}' should be string")
    
    if errors:
        raise ValueError(f"Schema validation failed: {errors}")
    
    logger.info("Schema validation passed")
    return True

def main():
    """Main execution function."""
    logger.info("Starting merge and validation process")
    
    # Load processed data
    grace_df = load_processed_grace()
    noaa_df = load_processed_noaa()
    
    # Merge datasets
    merged_df = merge_datasets(grace_df, noaa_df)
    
    # Load and validate against schema
    schema = load_schema()
    validate_against_schema(merged_df, schema)
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Save merged data
    merged_df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Saved merged data to {OUTPUT_PATH}")
    logger.info(f"Output shape: {merged_df.shape}")
    logger.info("Merge and validation complete")

if __name__ == "__main__":
    main()
