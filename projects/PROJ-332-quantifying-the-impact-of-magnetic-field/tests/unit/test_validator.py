"""
Unit tests for the validator module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.validator import (
    load_schema,
    validate_dataframe_against_schema,
    validate_input_schema,
    validate_output_schema
)

# Test fixtures
@pytest.fixture
def sample_input_df():
    return pd.DataFrame({
        'discharge_id': [12345, 12346],
        'island_width': [0.02, 0.03],
        'tau_e': [0.5, 0.6],
        'q_profile': [[1.2, 1.3], [1.1, 1.2]]
    })

@pytest.fixture
def sample_output_df():
    return pd.DataFrame({
        'discharge_id': [12345, 12346],
        'island_width': [0.02, 0.03],
        'tau_e': [0.5, 0.6],
        'confinement_mode': ['L-mode', 'H-mode'],
        'resonant_surface_density': [2.5, 3.0]
    })

@pytest.fixture
def invalid_output_df():
    return pd.DataFrame({
        'discharge_id': [12345, 12346],
        'island_width': [0.02, 0.03],
        'tau_e': [0.5, 0.6],
        'confinement_mode': ['L-mode', 'INVALID_MODE'], # Should be L-mode or H-mode
        'resonant_surface_density': [2.5, 3.0]
    })

def test_load_schema_valid():
    """Test loading a valid schema file."""
    schema_path = Path(__file__).parent.parent.parent / 'contracts' / 'dataset.schema.yaml'
    assert schema_path.exists(), "Schema file missing for test"
    schema = load_schema(str(schema_path))
    assert 'fields' in schema
    assert schema['version'] is not None

def test_load_schema_missing_file():
    """Test loading a missing schema file raises error."""
    with pytest.raises(FileNotFoundError):
        load_schema("non_existent_schema.yaml")

def test_validate_dataframe_against_schema_input(sample_input_df):
    """Test validation of input schema."""
    schema_path = Path(__file__).parent.parent.parent / 'contracts' / 'dataset.schema.yaml'
    schema = load_schema(str(schema_path))
    is_valid, errors = validate_dataframe_against_schema(sample_input_df, schema)
    assert is_valid, f"Validation failed with errors: {errors}"

def test_validate_dataframe_missing_column(sample_input_df):
    """Test validation fails on missing required column."""
    # Remove a required column
    df = sample_input_df.drop(columns=['tau_e'])
    schema_path = Path(__file__).parent.parent.parent / 'contracts' / 'dataset.schema.yaml'
    schema = load_schema(str(schema_path))
    is_valid, errors = validate_dataframe_against_schema(df, schema)
    assert not is_valid
    assert any('tau_e' in str(e) for e in errors)

def test_validate_output_schema_valid(sample_output_df):
    """Test validation of valid output schema."""
    schema_path = Path(__file__).parent.parent.parent / 'contracts' / 'output.schema.yaml'
    assert validate_output_schema(sample_output_df, str(schema_path))

def test_validate_output_schema_invalid_mode(invalid_output_df):
    """Test validation fails on invalid confinement mode."""
    schema_path = Path(__file__).parent.parent.parent / 'contracts' / 'output.schema.yaml'
    with pytest.raises(ValueError):
        validate_output_schema(invalid_output_df, str(schema_path))

def test_validate_input_schema_wrapper(sample_input_df):
    """Test the wrapper function for input schema."""
    assert validate_input_schema(sample_input_df)