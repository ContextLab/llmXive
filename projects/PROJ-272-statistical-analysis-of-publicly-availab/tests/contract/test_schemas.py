"""
Contract tests for dataset schema validation.

This module validates that the cleaned dataset (data/interim/cleaned_adress.csv)
and the generated feature matrix (data/processed/features.csv) conform to the
schema definitions specified in specs/001-statistical-cognitive-decline/contracts/.

Dependencies:
- T008: Schema definitions must exist.
- T016: Cleaned dataset must exist.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
import pandas as pd
import yaml

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON Schema from the contracts directory.

    Args:
        schema_name: Name of the schema file (e.g., 'dataset.schema.yaml')

    Returns:
        The schema as a dictionary.
    """
    schema_path = get_path('contracts') / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_data(data_path: Path) -> pd.DataFrame:
    """
    Load a CSV dataset.

    Args:
        data_path: Path to the CSV file.

    Returns:
        Pandas DataFrame.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    logger.info(f"Loading data from {data_path}")
    return pd.read_csv(data_path)

def validate_dataframe_against_schema(
    df: pd.DataFrame, 
    schema: Dict[str, Any], 
    schema_name: str
) -> bool:
    """
    Validate that every row in a DataFrame conforms to the provided JSON Schema.

    Args:
        df: The DataFrame to validate.
        schema: The JSON Schema dictionary.
        schema_name: Name for logging purposes.

    Returns:
        True if all rows are valid, False otherwise.
    """
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check for missing required columns in the DataFrame
    df_columns = set(df.columns)
    required_set = set(required_fields)
    
    missing_cols = required_set - df_columns
    if missing_cols:
        logger.error(f"Missing required columns in {schema_name}: {missing_cols}")
        return False

    valid_count = 0
    invalid_count = 0
    errors: List[str] = []

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        
        # Convert types if necessary (jsonschema expects specific types)
        # Pandas might return numpy types or objects, we need to ensure compatibility
        clean_row: Dict[str, Any] = {}
        for key, value in row_dict.items():
            if pd.isna(value):
                clean_row[key] = None
            elif isinstance(value, (pd.Timestamp,)):
                clean_row[key] = str(value)
            else:
                clean_row[key] = value

        try:
            jsonschema.validate(instance=clean_row, schema=schema)
            valid_count += 1
        except jsonschema.ValidationError as e:
            invalid_count += 1
            errors.append(f"Row {idx}: {e.message}")
            if len(errors) > 10: # Limit error logging
                break

    if invalid_count > 0:
        logger.error(f"Validation failed for {schema_name}. "
                     f"Valid: {valid_count}, Invalid: {invalid_count}")
        for err in errors[:5]:
            logger.error(f"  - {err}")
        return False
    
    logger.info(f"Validation passed for {schema_name}. All {valid_count} rows are valid.")
    return True

def test_dataset_schema() -> bool:
    """
    Contract test: Validate data/interim/cleaned_adress.csv against dataset.schema.yaml.
    
    Returns:
        True if validation passes, False otherwise.
    """
    try:
        schema = load_schema('dataset.schema.yaml')
        data_path = get_path('interim') / 'cleaned_adress.csv'
        df = load_data(data_path)
        
        logger.info(f"Validating {len(df)} rows against dataset schema...")
        return validate_dataframe_against_schema(df, schema, "dataset.schema.yaml")
    except Exception as e:
        logger.error(f"Dataset schema validation failed with error: {e}")
        return False

def test_feature_schema() -> bool:
    """
    Contract test: Validate data/processed/features.csv against feature.schema.yaml.
    
    Note: This test is skipped if the features file does not exist yet 
    (e.g., if US2 is not complete), but returns False to indicate failure 
    of the contract if the file is expected.
    
    Returns:
        True if validation passes, False otherwise.
    """
    try:
        schema = load_schema('feature.schema.yaml')
        data_path = get_path('processed') / 'features.csv'
        
        if not data_path.exists():
            logger.warning(f"Feature data file not found: {data_path}. "
                           "Skipping feature schema validation (US2 may not be complete).")
            # Depending on strictness, this might be a failure or a skip.
            # For contract tests, missing expected data is usually a failure.
            return False
        
        df = load_data(data_path)
        logger.info(f"Validating {len(df)} rows against feature schema...")
        return validate_dataframe_against_schema(df, schema, "feature.schema.yaml")
    except Exception as e:
        logger.error(f"Feature schema validation failed with error: {e}")
        return False

def main():
    """
    Entry point for running contract tests.
    """
    logger.info("Starting Contract Tests for Dataset Schemas...")
    
    results = {}
    
    # Test 1: Dataset Schema
    logger.info("--- Test: Dataset Schema ---")
    results['dataset_schema'] = test_dataset_schema()
    
    # Test 2: Feature Schema (if applicable)
    logger.info("--- Test: Feature Schema ---")
    results['feature_schema'] = test_feature_schema()
    
    # Summary
    logger.info("--- Summary ---")
    all_passed = all(results.values())
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    if all_passed:
        logger.info("All contract tests PASSED.")
        return 0
    else:
        logger.error("One or more contract tests FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(main())