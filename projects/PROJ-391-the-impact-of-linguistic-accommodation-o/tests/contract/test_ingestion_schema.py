"""
Contract test for ingestion output schema (T015).

Validates that the output of code/data/ingestion.py conforms to 
contracts/dataset.schema.yaml.

This test should be run after the ingestion script has generated
data/processed/accommodation_metrics.csv.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml
import pandas as pd
from jsonschema import validate, ValidationError, Draft7Validator
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "accommodation_metrics.csv"


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_data(data_path: Path) -> pd.DataFrame:
    """Load the processed metrics CSV."""
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    return pd.read_csv(data_path)


def convert_dataframe_to_schema_format(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convert pandas DataFrame to list of dicts for JSON schema validation.
    Handles potential NaN values by converting them to None.
    """
    # Replace NaN with None for JSON compatibility
    df_clean = df.where(pd.notnull(df), None)
    return df_clean.to_dict(orient='records')


def test_schema_file_exists():
    """Verify the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"


def test_data_file_exists():
    """Verify the ingestion output file exists."""
    assert OUTPUT_PATH.exists(), (
        f"Data file missing: {OUTPUT_PATH}. "
        "Run code/data/ingestion.py first to generate this file."
    )


def test_schema_is_valid_json_schema():
    """Verify the schema itself is valid."""
    schema = load_schema(SCHEMA_PATH)
    # Attempt to compile the schema to catch syntax errors
    try:
        Draft7Validator.check_schema(schema)
    except Exception as e:
        pytest.fail(f"Invalid JSON Schema: {e}")


def test_ingestion_output_matches_schema():
    """
    Main contract test: Validate that the ingestion output matches the schema.
    
    This ensures that:
    1. All required columns are present
    2. Data types match expectations
    3. No null values exist in required fields
    4. Structure conforms to the defined schema
    """
    # Load schema and data
    schema = load_schema(SCHEMA_PATH)
    df = load_data(OUTPUT_PATH)
    
    # Convert to schema format
    data_records = convert_dataframe_to_schema_format(df)
    
    # Validate against schema
    try:
        validate(instance=data_records, schema=schema)
    except ValidationError as e:
        pytest.fail(
            f"Data validation failed against schema:\n"
            f"Path: {' -> '.join(str(p) for p in e.path)}\n"
            f"Message: {e.message}\n"
            f"Instance: {e.instance}\n"
            f"Schema path: {' -> '.join(str(p) for p in e.schema_path)}"
        )


def test_required_columns_present():
    """
    Explicit check for required columns defined in the schema.
    Provides clearer error messages than generic schema validation.
    """
    schema = load_schema(SCHEMA_PATH)
    df = load_data(OUTPUT_PATH)
    
    # Extract required fields from schema
    required_fields = schema.get('items', {}).get('required', [])
    
    missing_columns = [col for col in required_fields if col not in df.columns]
    
    if missing_columns:
        pytest.fail(
            f"Missing required columns in output: {missing_columns}. "
            f"Required: {required_fields}, Found: {list(df.columns)}"
        )


def test_no_nulls_in_required_fields():
    """
    Verify that required fields contain no null/NaN values.
    """
    schema = load_schema(SCHEMA_PATH)
    df = load_data(OUTPUT_PATH)
    
    required_fields = schema.get('items', {}).get('required', [])
    
    for field in required_fields:
        if field in df.columns:
            null_count = df[field].isna().sum()
            if null_count > 0:
                pytest.fail(
                    f"Required field '{field}' contains {null_count} null values. "
                    "All required fields must be non-null."
                )


def test_column_types_match_schema():
    """
    Verify that column data types match schema expectations.
    """
    schema = load_schema(SCHEMA_PATH)
    df = load_data(OUTPUT_PATH)
    
    properties = schema.get('items', {}).get('properties', {})
    
    for col_name, col_schema in properties.items():
        if col_name in df.columns:
            expected_type = col_schema.get('type')
            actual_dtype = str(df[col_name].dtype)
            
            # Basic type mapping
            type_mapping = {
                'string': ['object', 'str', 'datetime64[ns]'],
                'number': ['float64', 'float32', 'int64', 'int32'],
                'integer': ['int64', 'int32', 'int16', 'int8'],
                'boolean': ['bool']
            }
            
            expected_types = type_mapping.get(expected_type, [expected_type])
            
            if actual_dtype not in expected_types:
                # Allow some flexibility for numeric types
                if expected_type in ['number', 'integer'] and actual_dtype.startswith('int'):
                    continue
                if expected_type in ['number', 'integer'] and actual_dtype.startswith('float'):
                    continue
                    
                pytest.fail(
                    f"Column '{col_name}' has type '{actual_dtype}' but schema expects '{expected_type}'"
                )