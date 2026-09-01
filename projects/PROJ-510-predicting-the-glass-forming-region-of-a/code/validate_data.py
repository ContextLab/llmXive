"""
Data Validation Module for Glass Forming Region Prediction.

This module validates processed alloy data against the defined schema
and ensures minimum data availability requirements are met.
"""
import logging
import sys
import os
import yaml
import json
import jsonschema
import pandas as pd
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
MIN_ROWS_WARNING = 500
MIN_ROWS_ERROR = 500
DATA_PATH = "data/processed/processed_alloys.csv"
SCHEMA_PATH = "contracts/dataset.schema.yaml"

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from YAML file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Convert JSON schema from YAML if needed
    # The schema should already be a dict representing JSON schema
    return schema

def load_processed_data(data_path: str) -> pd.DataFrame:
    """Load processed alloy data from CSV."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from {data_path}")
    return df

def validate_schema_compliance(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate DataFrame against JSON schema.
    
    Checks:
    - Required columns exist
    - Data types are compatible (basic check)
    - No null values in required fields
    """
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required columns
    missing_columns = [col for col in required_fields if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Check for null values in required fields
    for field in required_fields:
        if field in df.columns:
            null_count = df[field].isnull().sum()
            if null_count > 0:
                logger.warning(f"Column '{field}' has {null_count} null values")
    
    # Basic type validation (check if numeric columns are actually numeric)
    for field, props in properties.items():
        if field in df.columns:
            expected_type = props.get('type')
            if expected_type == 'number':
                if not pd.api.types.is_numeric_dtype(df[field]):
                    logger.warning(f"Column '{field}' should be numeric but is {df[field].dtype}")
            elif expected_type == 'string':
                if not pd.api.types.is_string_dtype(df[field]):
                    logger.warning(f"Column '{field}' should be string but is {df[field].dtype}")
    
    logger.info("Schema validation passed")
    return True

def validate_data_availability(df: pd.DataFrame) -> bool:
    """
    Validate minimum data availability.
    
    Requirements:
    - Row count >= 500 (error if below)
    - Log INFO if 500 <= N < 1000
    """
    row_count = len(df)
    
    if row_count < MIN_ROWS_ERROR:
        raise ValueError(f"Data availability error: {row_count} valid entries (minimum required: {MIN_ROWS_ERROR})")
    
    if MIN_ROWS_ERROR <= row_count < 1000:
        logger.info(f"Data availability is low: {row_count} rows (500 <= N < 1000)")
    else:
        logger.info(f"Data availability check passed: {row_count} rows")
    
    return True

def run_validation(data_path: str = DATA_PATH, schema_path: str = SCHEMA_PATH) -> Dict[str, Any]:
    """
    Run full validation pipeline on processed data.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        'success': False,
        'row_count': 0,
        'schema_valid': False,
        'availability_valid': False,
        'errors': []
    }
    
    try:
        # Load data
        logger.info(f"Loading data from {data_path}")
        df = load_processed_data(data_path)
        results['row_count'] = len(df)
        
        # Load schema
        logger.info(f"Loading schema from {schema_path}")
        schema = load_schema(schema_path)
        
        # Validate schema compliance
        logger.info("Validating schema compliance...")
        validate_schema_compliance(df, schema)
        results['schema_valid'] = True
        
        # Validate data availability
        logger.info("Validating data availability...")
        validate_data_availability(df)
        results['availability_valid'] = True
        
        results['success'] = True
        logger.info("All validation checks passed!")
        
    except FileNotFoundError as e:
        error_msg = str(e)
        logger.error(f"File not found: {error_msg}")
        results['errors'].append(error_msg)
        
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"Validation error: {error_msg}")
        results['errors'].append(error_msg)
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        results['errors'].append(error_msg)
    
    return results

def main():
    """Main entry point for data validation."""
    logger.info("Starting data validation pipeline")
    
    results = run_validation()
    
    # Print summary
    print("\n" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)
    print(f"Success: {results['success']}")
    print(f"Row Count: {results['row_count']}")
    print(f"Schema Valid: {results['schema_valid']}")
    print(f"Availability Valid: {results['availability_valid']}")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("="*50)
    
    # Exit with appropriate code
    if results['success']:
        logger.info("Validation completed successfully")
        sys.exit(0)
    else:
        logger.error("Validation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()