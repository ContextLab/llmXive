"""
Contract test for data schema validation.
Validates that data artifacts conform to the schema defined in
specs/001-chemo-biomarker-discovery/contracts/dataset.schema.yaml.
"""
import os
import sys
import json
import yaml
from pathlib import Path
import pytest

# Add project root to path to ensure imports work
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.contract.test_schema_validation import (
    load_schema,
    validate_type,
    validate_required_fields,
    validate_data_against_schema
)

# Constants
SCHEMA_PATH = project_root / "specs" / "001-chemo-biomarker-discovery" / "contracts" / "dataset.schema.yaml"
PROCESSED_DATA_DIR = project_root / "data" / "processed"


def get_sample_data_files():
    """
    Discover sample data files in the processed directory to validate.
    Returns a list of paths to CSV/Parquet files.
    """
    if not PROCESSED_DATA_DIR.exists():
        return []
    
    files = []
    for ext in ["*.csv", "*.parquet"]:
        files.extend(list(PROCESSED_DATA_DIR.glob(ext)))
    return files


def test_schemas_exist():
    """Test that the dataset schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"


def test_schema_loads_valid_yaml():
    """Test that the schema file is valid YAML."""
    schema = load_schema(SCHEMA_PATH)
    assert schema is not None
    assert "type" in schema
    assert "properties" in schema


def test_dataset_schema_structure():
    """Test that the dataset schema has the expected structure."""
    schema = load_schema(SCHEMA_PATH)
    
    # Check required top-level fields
    assert "type" in schema
    assert "properties" in schema
    
    # Check for expected properties based on project requirements
    properties = schema["properties"]
    expected_properties = [
        "tumor_type",
        "sample_id",
        "response_label",
        "gene_expression"
    ]
    
    for prop in expected_properties:
        assert prop in properties, f"Expected property '{prop}' missing from schema"


def test_validate_data_against_schema():
    """
    Test validation logic against real data files if they exist.
    If no processed data exists yet, this test is skipped (not failed).
    """
    data_files = get_sample_data_files()
    
    if not data_files:
        pytest.skip("No processed data files found to validate. "
                   "Run data acquisition tasks first.")
    
    schema = load_schema(SCHEMA_PATH)
    
    for file_path in data_files:
        # Load data
        if file_path.suffix == ".csv":
            import pandas as pd
            data = pd.read_csv(file_path).to_dict(orient="records")
        elif file_path.suffix == ".parquet":
            import pandas as pd
            data = pd.read_parquet(file_path).to_dict(orient="records")
        else:
            continue
        
        # Validate
        try:
            validate_data_against_schema(data, schema)
        except AssertionError as e:
            pytest.fail(f"Data file {file_path} failed schema validation: {str(e)}")


def test_required_fields_validation():
    """Test that required fields are enforced by the validation logic."""
    schema = load_schema(SCHEMA_PATH)
    
    # Test with missing required field
    invalid_data = [{"sample_id": "S1", "gene_expression": {"GENE1": 1.0}}]
    
    with pytest.raises(AssertionError):
        validate_required_fields(invalid_data, schema)


def test_type_validation():
    """Test that type validation works correctly."""
    # Test valid types
    assert validate_type("string", "hello") is True
    assert validate_type("integer", 42) is True
    assert validate_type("number", 3.14) is True
    assert validate_type("boolean", True) is True
    assert validate_type("object", {"key": "value"}) is True
    assert validate_type("array", [1, 2, 3]) is True
    
    # Test invalid types
    assert validate_type("integer", "42") is False
    assert validate_type("string", 123) is False


def test_specific_field_types():
    """Test validation of specific fields defined in the schema."""
    schema = load_schema(SCHEMA_PATH)
    
    # Check tumor_type is string
    assert "tumor_type" in schema["properties"]
    tumor_type_schema = schema["properties"]["tumor_type"]
    assert tumor_type_schema["type"] == "string"
    
    # Check response_label is string (or potentially categorical)
    assert "response_label" in schema["properties"]
    response_schema = schema["properties"]["response_label"]
    assert response_schema["type"] == "string"


def test_sample_data_validation():
    """
    Create a minimal valid sample record and validate it.
    This ensures the schema can accept properly formatted data.
    """
    schema = load_schema(SCHEMA_PATH)
    
    # Create a minimal valid record
    valid_record = {
        "tumor_type": "BRCA",
        "sample_id": "TCGA-XX-XXXX",
        "response_label": "Responder",
        "gene_expression": {"TP53": 10.5, "BRCA1": 5.2}
    }
    
    # Should not raise
    validate_data_against_schema([valid_record], schema)


def test_invalid_data_catches_error():
    """Test that invalid data is properly rejected."""
    schema = load_schema(SCHEMA_PATH)
    
    # Invalid record: missing required field
    invalid_record = {
        "tumor_type": "BRCA",
        # Missing sample_id
        "response_label": "Responder",
        "gene_expression": {"TP53": 10.5}
    }
    
    with pytest.raises(AssertionError):
        validate_data_against_schema([invalid_record], schema)