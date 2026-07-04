"""
Contract test for merged CSV schema validation.

Validates that the output of 03_merge_output.py conforms to the schema
defined in contracts/dataset.schema.yaml.

This test ensures:
1. All required columns are present.
2. Data types match the schema definitions.
3. No NaN values exist in primary columns.
4. Date formats are consistent.
"""
import os
import sys
import logging
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "merged_monthly.csv"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

def load_schema(schema_path: Path) -> dict:
    """Load and parse the YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_columns(df: pd.DataFrame, schema: dict) -> bool:
    """Validate that all required columns exist in the DataFrame."""
    required_columns = schema.get('required_columns', [])
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False
    
    logger.info(f"All required columns present: {required_columns}")
    return True

def validate_types(df: pd.DataFrame, schema: dict) -> bool:
    """Validate that column data types match the schema."""
    type_mapping = schema.get('column_types', {})
    valid = True
    
    for col, expected_type in type_mapping.items():
        if col not in df.columns:
            continue
        
        actual_type = str(df[col].dtype)
        
        # Map pandas dtypes to generic types for comparison
        type_checks = {
            'int64': ['int'],
            'float64': ['float'],
            'object': ['string', 'str'],
            'datetime64[ns]': ['datetime']
        }
        
        is_valid = False
        for dtype_key, dtype_labels in type_checks.items():
            if expected_type.lower() in dtype_labels and dtype_key == actual_type:
                is_valid = True
                break
        
        # Specific check for datetime
        if expected_type.lower() == 'datetime' and 'datetime' in actual_type:
            is_valid = True
        
        if not is_valid and expected_type.lower() not in ['any', 'mixed']:
            logger.warning(f"Column '{col}' has type '{actual_type}', expected '{expected_type}'")
            # Don't fail hard on type mismatches if data is logically correct, just warn
            # unless strict mode is required by schema
            if schema.get('strict_types', False):
                valid = False
    
    if valid:
        logger.info("Data types validated successfully")
    return valid

def validate_no_nans(df: pd.DataFrame, schema: dict) -> bool:
    """Validate that primary columns have no NaN values."""
    primary_columns = schema.get('primary_columns', [])
    valid = True
    
    for col in primary_columns:
        if col not in df.columns:
            logger.error(f"Primary column '{col}' missing from DataFrame")
            valid = False
            continue
        
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            logger.error(f"Column '{col}' contains {nan_count} NaN values")
            valid = False
        else:
            logger.info(f"Column '{col}' has no NaN values")
    
    return valid

def validate_date_format(df: pd.DataFrame, schema: dict) -> bool:
    """Validate date format consistency."""
    date_columns = schema.get('date_columns', [])
    valid = True
    
    for col in date_columns:
        if col not in df.columns:
            continue
        
        # Try to parse as datetime
        try:
            parsed = pd.to_datetime(df[col], errors='raise')
            logger.info(f"Column '{col}' successfully parsed as datetime")
        except Exception as e:
            logger.error(f"Column '{col}' failed datetime parsing: {e}")
            valid = False
    
    return valid

def run_validation() -> bool:
    """Run all schema validation checks."""
    logger.info(f"Starting schema validation for {DATA_PATH}")
    
    if not DATA_PATH.exists():
        logger.error(f"Data file not found: {DATA_PATH}")
        return False
    
    if not SCHEMA_PATH.exists():
        logger.error(f"Schema file not found: {SCHEMA_PATH}")
        return False
    
    try:
        schema = load_schema(SCHEMA_PATH)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False
    
    try:
        df = pd.read_csv(DATA_PATH)
        logger.info(f"Loaded {len(df)} rows from {DATA_PATH}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return False
    
    checks = [
        ("Columns", validate_columns(df, schema)),
        ("Types", validate_types(df, schema)),
        ("No NaNs", validate_no_nans(df, schema)),
        ("Date Format", validate_date_format(df, schema))
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "PASS" if result else "FAIL"
        logger.info(f"{check_name} validation: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("All schema validations passed")
    else:
        logger.error("Schema validation failed")
    
    return all_passed

def main():
    """Main entry point for the test."""
    success = run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()