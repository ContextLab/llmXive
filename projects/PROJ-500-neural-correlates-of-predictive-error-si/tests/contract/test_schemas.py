import json
import os
import pytest
from pathlib import Path
import yaml
import pandas as pd
from jsonschema import validate, ValidationError, Draft7Validator

# Project root handling
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = ROOT_DIR / "contracts"
DATA_DIR = ROOT_DIR / "data"

def load_schema(schema_name: str) -> dict:
    """Load a JSON Schema from the contracts directory."""
    schema_path = CONTRACTS_DIR / f"{schema_name}.yaml"
    if not schema_path.exists():
        # Fallback to .json if yaml not found, though spec says yaml
        schema_path = CONTRACTS_DIR / f"{schema_name}.json"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        if schema_path.suffix == '.yaml':
            return yaml.safe_load(f)
        else:
            return json.load(f)

def validate_data_against_schema(data_path: Path, schema_name: str) -> bool:
    """
    Validates a CSV file against a JSON Schema.
    Since JSON Schema is for JSON objects, we validate the structure of the 
    CSV headers and optionally a sample row against the schema definitions.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    schema = load_schema(schema_name)
    validator = Draft7Validator(schema)

    # Read CSV to check headers (keys)
    df = pd.read_csv(data_path)
    columns = list(df.columns)
    
    # The schema usually defines 'properties' for the object structure.
    # We map CSV columns to schema properties.
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    # Check 1: All required fields present in CSV
    missing_fields = set(required_fields) - set(columns)
    if missing_fields:
        raise ValidationError(f"Missing required fields in {data_path.name}: {missing_fields}")

    # Check 2: Validate types of a sample row (if types are defined in schema)
    # We convert the first row to a dict for validation
    if len(df) > 0:
        sample_row = df.iloc[0].to_dict()
        
        # JSON Schema validation expects a JSON object. 
        # We perform a manual type check based on schema definitions 
        # because jsonschema.validate expects a pure JSON-compatible dict.
        for field, schema_def in properties.items():
            if field in sample_row:
                value = sample_row[field]
                expected_type = schema_def.get('type')
                
                if expected_type == 'number':
                    if not isinstance(value, (int, float)):
                        # Allow numeric strings if they can be converted, but strict check usually preferred
                        try:
                            float(value)
                        except (ValueError, TypeError):
                            raise ValidationError(f"Field '{field}' is expected to be number, got {type(value)}")
                elif expected_type == 'string':
                    if not isinstance(value, str):
                        # Allow int/float to be cast to string, but strict check preferred
                        pass 
                elif expected_type == 'integer':
                    if not isinstance(value, int):
                        try:
                            int(value)
                        except (ValueError, TypeError):
                            raise ValidationError(f"Field '{field}' is expected to be integer, got {type(value)}")
                # Boolean, array, object checks omitted for CSV simplicity unless strictly needed

    return True

def test_aligned_data_schema_exists():
    """Test that the aligned_data schema file exists."""
    schema_path = CONTRACTS_DIR / "aligned_data.yaml"
    assert schema_path.exists(), f"Schema file missing: {schema_path}"

def test_model_output_schema_exists():
    """Test that the model_output schema file exists."""
    schema_path = CONTRACTS_DIR / "model_output.yaml"
    assert schema_path.exists(), f"Schema file missing: {schema_path}"

def test_aligned_data_schema_valid():
    """Test that the aligned_data schema itself is valid JSON Schema Draft 7."""
    schema = load_schema("aligned_data")
    Draft7Validator.check_schema(schema)

def test_model_output_schema_valid():
    """Test that the model_output schema itself is valid JSON Schema Draft 7."""
    schema = load_schema("model_output")
    Draft7Validator.check_schema(schema)

def test_aligned_data_schema_validation():
    """
    T018: Contract test for aligned_data schema.
    Validates that the final data/aligned_data.csv contains all required fields
    including 'learning_phase'.
    """
    aligned_data_path = DATA_DIR / "aligned_data.csv"
    
    # If the file doesn't exist, we can't validate it. 
    # In a CI/CD or pipeline context, this would fail the build if the file is expected.
    if not aligned_data_path.exists():
        pytest.skip(f"Data file {aligned_data_path} not found. Skipping validation.")
    
    # Validate structure against schema
    validate_data_against_schema(aligned_data_path, "aligned_data")

    # Specific check for T018 requirement: 'learning_phase' must exist
    df = pd.read_csv(aligned_data_path)
    assert 'learning_phase' in df.columns, (
        "Contract violation: 'learning_phase' column is missing from aligned_data.csv. "
        "This field is required for the LME model (FR-006)."
    )

    # Verify 'learning_phase' has valid categorical values (non-null)
    assert df['learning_phase'].notna().all(), (
        "Contract violation: 'learning_phase' column contains null values."
    )

    # Verify unique values are reasonable (e.g., 'Early', 'Late')
    unique_phases = df['learning_phase'].unique()
    valid_phases = {'Early', 'Late', 'Mid', 'Initial', 'Final'} # Common binning names
    # We allow any string, but check that they are not empty or NaN (handled above)
    assert all(isinstance(p, str) and len(p) > 0 for p in unique_phases), (
        "Contract violation: 'learning_phase' contains invalid empty or non-string values."
    )