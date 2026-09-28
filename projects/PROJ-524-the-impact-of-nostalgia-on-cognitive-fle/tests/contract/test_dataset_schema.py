"""
Contract test for dataset schema validation.

This test validates that the cleaned dataset conforms to the schema defined
in `contracts/dataset.schema.yaml`. It ensures that all required fields are
present, have the correct types, and satisfy the constraints defined in the
contract.

Dependencies:
  - T020a-2: Contracts generation and validation must be complete.

Run with:
  pytest tests/contract/test_dataset_schema.py -v
"""

import os
import json
import pytest
import pandas as pd
import yaml
from pathlib import Path

# Import config to get paths
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from config import get_config


def load_schema(schema_path: str) -> dict:
    """Load the JSON schema from the contracts directory."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_field_type(value, expected_type: str) -> bool:
    """Validate that a value matches the expected type."""
    if pd.isna(value):
        return True  # Nulls are handled by 'required' constraints
    
    type_map = {
        'integer': int,
        'number': (int, float),
        'string': str,
        'boolean': bool
    }
    
    expected = type_map.get(expected_type)
    if expected is None:
        raise ValueError(f"Unknown type: {expected_type}")
    
    return isinstance(value, expected)

def validate_constraint(value, constraint_type: str, constraint_value) -> bool:
    """Validate a value against a specific constraint."""
    if pd.isna(value):
        return True  # Nulls handled elsewhere
    
    if constraint_type == 'minimum':
        return value >= constraint_value
    elif constraint_type == 'maximum':
        return value <= constraint_value
    elif constraint_type == 'pattern':
        import re
        return bool(re.match(constraint_value, str(value)))
    elif constraint_type == 'enum':
        return value in constraint_value
    return True

def validate_record(record: dict, schema: dict) -> list:
    """Validate a single record against the schema. Returns list of errors."""
    errors = []
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])
    
    # Check required fields
    for field in required_fields:
        if field not in record or pd.isna(record.get(field)):
            errors.append(f"Missing required field: {field}")
    
    # Check field types and constraints
    for field, value in record.items():
        if field not in properties:
            errors.append(f"Unknown field: {field}")
            continue
        
        field_schema = properties[field]
        
        # Type validation
        if 'type' in field_schema:
            if not validate_field_type(value, field_schema['type']):
                errors.append(f"Field '{field}' has wrong type. Expected {field_schema['type']}, got {type(value)}")
        
        # Constraint validation
        for constraint in ['minimum', 'maximum', 'pattern', 'enum']:
            if constraint in field_schema:
                if not validate_constraint(value, constraint, field_schema[constraint]):
                    errors.append(f"Field '{field}' violates {constraint} constraint: {field_schema[constraint]}")
    
    return errors

@pytest.fixture
def schema():
    """Load the dataset schema."""
    config = get_config()
    schema_path = config['contracts_dir'] / 'dataset.schema.yaml'
    if not schema_path.exists():
        pytest.skip(f"Schema file not found at {schema_path}. Run T020a-1 first.")
    return load_schema(schema_path)

@pytest.fixture
def cleaned_dataset_path():
    """Path to the cleaned dataset."""
    config = get_config()
    return config['processed_dir'] / 'cleaned_dataset.csv'

@pytest.mark.contract
def test_schema_exists(schema):
    """Test that the schema is valid and contains expected structure."""
    assert schema is not None
    assert 'properties' in schema
    assert 'required' in schema
    # Check for expected primary keys
    assert 'participant_id' in schema['properties']
    assert 'stimulus_type' in schema['properties']

@pytest.mark.contract
def test_required_fields_present(cleaned_dataset_path, schema):
    """Test that all required fields from the schema exist in the dataset."""
    if not cleaned_dataset_path.exists():
        pytest.skip(f"Cleaned dataset not found at {cleaned_dataset_path}. Run ingestion pipeline first.")
    
    df = pd.read_csv(cleaned_dataset_path)
    required_fields = schema.get('required', [])
    
    missing = [f for f in required_fields if f not in df.columns]
    assert len(missing) == 0, f"Missing required columns: {missing}"

@pytest.mark.contract
def test_field_types(cleaned_dataset_path, schema):
    """Test that data types match the schema definition."""
    if not cleaned_dataset_path.exists():
        pytest.skip(f"Cleaned dataset not found at {cleaned_dataset_path}. Run ingestion pipeline first.")
    
    df = pd.read_csv(cleaned_dataset_path)
    properties = schema.get('properties', {})
    
    errors = []
    for col in df.columns:
        if col in properties:
            expected_type = properties[col].get('type')
            if expected_type == 'integer':
                if not pd.api.types.is_integer_dtype(df[col]) and not pd.api.types.is_float_dtype(df[col]):
                    errors.append(f"Column '{col}' is not numeric (expected integer)")
            elif expected_type == 'string':
                if not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                    errors.append(f"Column '{col}' is not string")
    
    assert len(errors) == 0, f"Type validation errors: {errors}"

@pytest.mark.contract
def test_constraints(cleaned_dataset_path, schema):
    """Test that data values satisfy schema constraints."""
    if not cleaned_dataset_path.exists():
        pytest.skip(f"Cleaned dataset not found at {cleaned_dataset_path}. Run ingestion pipeline first.")
    
    df = pd.read_csv(cleaned_dataset_path)
    properties = schema.get('properties', {})
    errors = []
    
    for col, constraints in properties.items():
        if col not in df.columns:
            continue
        
        # Check minimum
        if 'minimum' in constraints:
            min_val = constraints['minimum']
            if df[col].notna().any():
                if df[col].min() < min_val:
                    errors.append(f"Column '{col}' has values below minimum {min_val}")
        
        # Check maximum
        if 'maximum' in constraints:
            max_val = constraints['maximum']
            if df[col].notna().any():
                if df[col].max() > max_val:
                    errors.append(f"Column '{col}' has values above maximum {max_val}")
        
        # Check enum
        if 'enum' in constraints:
            valid_values = set(constraints['enum'])
            if df[col].notna().any():
                invalid = set(df[col].dropna().unique()) - valid_values
                if invalid:
                    errors.append(f"Column '{col}' has invalid enum values: {invalid}")
    
    assert len(errors) == 0, f"Constraint validation errors: {errors}"

@pytest.mark.contract
def test_record_level_validation(cleaned_dataset_path, schema):
    """Test individual records against the full schema."""
    if not cleaned_dataset_path.exists():
        pytest.skip(f"Cleaned dataset not found at {cleaned_dataset_path}. Run ingestion pipeline first.")
    
    df = pd.read_csv(cleaned_dataset_path)
    total_errors = 0
    
    # Sample a subset of records to avoid memory issues if dataset is huge
    sample_size = min(100, len(df))
    sample_df = df.sample(n=sample_size, random_state=42)
    
    for idx, row in sample_df.iterrows():
        record = row.to_dict()
        errors = validate_record(record, schema)
        if errors:
            total_errors += len(errors)
            # Log first few errors for debugging
            if total_errors <= 5:
                print(f"Record {idx} errors: {errors}")
    
    assert total_errors == 0, f"Found {total_errors} record-level validation errors"

@pytest.mark.contract
def test_schema_compliance_summary(cleaned_dataset_path, schema):
    """Generate a summary of schema compliance."""
    if not cleaned_dataset_path.exists():
        pytest.skip(f"Cleaned dataset not found at {cleaned_dataset_path}. Run ingestion pipeline first.")
    
    df = pd.read_csv(cleaned_dataset_path)
    required = schema.get('required', [])
    
    # Check completeness
    completeness = {}
    for col in required:
        if col in df.columns:
            completeness[col] = df[col].notna().sum() / len(df)
        else:
            completeness[col] = 0.0
    
    # Assert that all required fields have > 90% completeness
    for col, rate in completeness.items():
        assert rate > 0.90, f"Field '{col}' has low completeness: {rate:.2%}"