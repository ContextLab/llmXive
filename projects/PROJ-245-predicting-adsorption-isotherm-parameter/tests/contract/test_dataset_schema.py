"""
Contract test for dataset schema compliance.
Ensures that the dataset conforms to the structure defined in contracts/dataset.schema.yaml.
"""
import pytest
import pandas as pd
import yaml
from pathlib import Path
from code.data.validate_schema import load_schema, validate_dataframe

@pytest.fixture
def schema_path():
    """Return the path to the dataset schema file."""
    return Path("contracts/dataset.schema.yaml")

@pytest.fixture
def sample_valid_data():
    """
    Create a DataFrame that should comply with the schema.
    Includes all required fields with correct types as per typical schema definitions.
    """
    data = {
        'material_id': ['M1', 'M2', 'M3'],
        'adsorbate_smiles': ['CCO', 'c1ccccc1', 'CC(=O)O'],
        'surface_area': [100.0, 200.0, 300.0],
        'pore_volume': [0.1, 0.2, 0.3],
        'polarizability': [1.0, 2.0, 3.0],
        'kinetic_diameter': [3.0, 4.0, 5.0],
        'langmuir_capacity': [10.0, 20.0, 30.0],
        'henry_constant': [0.1, 0.2, 0.3],
        'isotherm_type': ['Type I', 'Type I', 'Type II']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_invalid_data():
    """
    Create a DataFrame that violates the schema.
    Contains invalid columns and wrong data types.
    """
    data = {
        'material_id': ['M1', 'M2'],
        'invalid_column': ['value1', 'value2'],  # Not in schema
        'surface_area': ['not_a_number', 200.0]  # Wrong type (string instead of float)
    }
    return pd.DataFrame(data)

def test_load_schema(schema_path):
    """Test that the schema can be loaded successfully."""
    schema = load_schema(schema_path)
    assert schema is not None, "Schema should not be None"
    assert 'fields' in schema, "Schema should contain 'fields' key"
    assert len(schema['fields']) > 0, "Schema should have at least one field"

def test_validate_valid_data(schema_path, sample_valid_data):
    """Test that valid data passes schema validation."""
    schema = load_schema(schema_path)
    is_valid, errors = validate_dataframe(sample_valid_data, schema)
    
    assert is_valid, f"Valid data should pass validation. Errors: {errors}"
    assert len(errors) == 0, f"No errors expected. Got: {errors}"

def test_validate_invalid_data(schema_path, sample_invalid_data):
    """Test that invalid data fails schema validation."""
    schema = load_schema(schema_path)
    is_valid, errors = validate_dataframe(sample_invalid_data, schema)
    
    assert not is_valid, "Invalid data should fail validation"
    assert len(errors) > 0, "Should have validation errors"
    
    # Check that specific errors are reported
    error_messages = [str(e) for e in errors]
    assert any("invalid_column" in msg for msg in error_messages), \
        "Should report error for invalid column"
    assert any("surface_area" in msg for msg in error_messages), \
        "Should report error for surface_area type mismatch"

def test_validate_missing_required_fields(schema_path):
    """Test that data missing required fields fails validation."""
    # Create data missing 'material_id' (required field)
    data = {
        'adsorbate_smiles': ['CCO', 'c1ccccc1'],
        'surface_area': [100.0, 200.0]
    }
    df = pd.DataFrame(data)
    
    schema = load_schema(schema_path)
    is_valid, errors = validate_dataframe(df, schema)
    
    assert not is_valid, "Data missing required fields should fail validation"
    assert any("material_id" in str(e) for e in errors), \
        "Should report error for missing material_id"

def test_validate_processed_data_integration(schema_path):
    """
    Integration test: Validate that the output of the preprocessing pipeline
    (if it existed) would match the schema. This ensures the contract holds
    between data generation and downstream consumption.
    """
    # Simulate the output of code/data/preprocess.py based on T015 requirements
    # Required columns: polarizability, langmuir_capacity, henry_constant, surface_area
    # Plus standard identifiers
    data = {
        'material_id': ['MOF-5-001', 'HKUST-1-002'],
        'adsorbate_smiles': ['CC', 'O'],
        'surface_area': [1500.5, 2200.1],
        'pore_volume': [0.8, 1.1],
        'polarizability': [2.5, 1.2],
        'kinetic_diameter': [4.0, 3.0],
        'langmuir_capacity': [5.5, 10.2],
        'henry_constant': [0.05, 0.12],
        'isotherm_type': ['Type I', 'Type I']
    }
    df = pd.DataFrame(data)
    
    schema = load_schema(schema_path)
    is_valid, errors = validate_dataframe(df, schema)
    
    assert is_valid, f"Processed data must conform to schema. Errors: {errors}"