"""
Contract test for data schema validation.

This test validates that the processed dataset (Parquet/CSV) conforms to
the expected schema defined in data/schemas/static_schema.yaml.

It ensures:
1. All required fields are present (smiles, node_features, edge_features, 
   surface_area, molecular_weight)
2. Data types match the schema definitions
3. Values satisfy constraints (e.g., surface_area >= 0)
4. No missing values in critical columns for the training set
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
import yaml
from jsonschema import validate, ValidationError, Draft7Validator

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.config import get_data_dir

logger = get_logger(__name__)

# Path to the schema file
SCHEMA_PATH = project_root / "data" / "schemas" / "static_schema.yaml"

# Path to the processed data (output of T014)
PROCESSED_DATA_PATH = project_root / "data" / "processed" / "graphs_with_features.parquet"

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON/YAML schema from disk."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Convert JSON Schema draft version if needed
    # Ensure we have a valid JSON Schema
    if '$schema' not in schema:
        schema['$schema'] = 'http://json-schema.org/draft-07/schema#'
    
    return schema

def convert_row_to_dict(row: pd.Series) -> Dict[str, Any]:
    """
    Convert a pandas Series row to a dictionary suitable for JSON Schema validation.
    Handles numpy types and converts arrays to lists.
    """
    result = {}
    for key, value in row.items():
        if isinstance(value, np.ndarray):
            result[key] = value.tolist()
        elif isinstance(value, (np.int64, np.int32)):
            result[key] = int(value)
        elif isinstance(value, (np.float64, np.float32)):
            result[key] = float(value)
        elif pd.isna(value):
            result[key] = None
        else:
            result[key] = value
    return result

def validate_schema_compliance(data_path: Path, schema: Dict[str, Any]) -> List[str]:
    """
    Validate that the dataset conforms to the schema.
    
    Returns a list of error messages if validation fails.
    """
    errors = []
    
    if not data_path.exists():
        errors.append(f"Data file not found: {data_path}")
        return errors
    
    try:
        # Load parquet file
        df = pd.read_parquet(data_path)
        logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        errors.append(f"Failed to load data file: {str(e)}")
        return errors
    
    # Check required columns
    required_columns = ['smiles', 'node_features', 'edge_features', 'surface_area', 'molecular_weight']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
        return errors
    
    # Validate each row against the schema
    validator = Draft7Validator(schema)
    
    for idx, row in df.iterrows():
        row_dict = convert_row_to_dict(row)
        validation_errors = list(validator.iter_errors(row_dict))
        
        if validation_errors:
            for error in validation_errors:
                error_msg = f"Row {idx}: {error.message} (path: {' -> '.join(map(str, error.path))})"
                errors.append(error_msg)
                # Limit error reporting to first 10 errors per row to avoid spam
                if len(errors) > 10:
                    break
            if len(errors) > 10:
                errors.append(f"... and more errors for row {idx}")
                break
    
    # Check for missing values in critical columns
    critical_columns = ['smiles', 'surface_area', 'molecular_weight']
    for col in critical_columns:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            errors.append(f"Column '{col}' has {missing_count} missing values")
    
    return errors

def test_schema_exists():
    """Test that the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"
    logger.info(f"Schema file found: {SCHEMA_PATH}")

def test_schema_is_valid_json():
    """Test that the schema file is valid JSON/YAML."""
    try:
        schema = load_schema(SCHEMA_PATH)
        # Basic validation of schema structure
        assert 'type' in schema, "Schema must have a 'type' field"
        assert schema['type'] == 'object', "Schema type must be 'object'"
        assert 'properties' in schema, "Schema must have 'properties'"
        assert 'required' in schema, "Schema must have 'required' fields"
        logger.info("Schema is valid JSON/YAML")
    except Exception as e:
        pytest.fail(f"Schema validation failed: {str(e)}")

def test_data_conforms_to_schema():
    """
    Main contract test: Validate that the processed dataset conforms to the schema.
    
    This test will FAIL if:
    1. The schema file is missing or invalid
    2. The data file is missing
    3. Required columns are missing
    4. Data types don't match the schema
    5. Values violate constraints (e.g., negative surface area)
    6. Missing values exist in critical columns
    """
    if not PROCESSED_DATA_PATH.exists():
        pytest.skip(f"Processed data file not found at {PROCESSED_DATA_PATH}. "
                   "This test requires T014 to be completed first.")
    
    try:
        schema = load_schema(SCHEMA_PATH)
        errors = validate_schema_compliance(PROCESSED_DATA_PATH, schema)
        
        if errors:
            logger.error("Schema validation failed with the following errors:")
            for error in errors[:10]:  # Log first 10 errors
                logger.error(f"  - {error}")
            if len(errors) > 10:
                logger.error(f"  ... and {len(errors) - 10} more errors")
            
            pytest.fail(f"Data schema validation failed: {len(errors)} errors found")
        else:
            logger.info("Data schema validation passed successfully")
            assert True
    
    except Exception as e:
        pytest.fail(f"Unexpected error during schema validation: {str(e)}")

def test_no_missing_values_in_target():
    """
    Specific test for US1 requirement: No missing values in the target column 
    (surface_area) for the training set.
    
    Note: This test assumes the full processed dataset is available.
    In a real pipeline, this would be run after splitting.
    """
    if not PROCESSED_DATA_PATH.exists():
        pytest.skip(f"Processed data file not found at {PROCESSED_DATA_PATH}.")
    
    try:
        df = pd.read_parquet(PROCESSED_DATA_PATH)
        missing_count = df['surface_area'].isna().sum()
        
        assert missing_count == 0, f"Found {missing_count} missing values in 'surface_area' column"
        logger.info("No missing values in 'surface_area' column")
    
    except Exception as e:
        pytest.fail(f"Error checking for missing values: {str(e)}")

if __name__ == "__main__":
    import pytest
    import sys
    
    # Run the tests
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)