"""
Unit tests for dataset schema validation.
"""
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import yaml

# Import the module under test
# Adjust import path based on project structure (src/utils/validate_schema.py)
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from utils.validate_schema import (
    load_schema, 
    validate_dataframe, 
    validate_and_raise, 
    validate_csv_file,
    SCHEMA_PATH
)


@pytest.fixture
def valid_schema():
    """Load the valid schema for testing."""
    return load_schema()


@pytest.fixture
def valid_dataframe(valid_schema):
    """Create a valid DataFrame based on the schema."""
    data = {
        'experiment_id': ['exp_001', 'exp_002'],
        'source': ['materials_project', 'nist'],
        'material_type': ['Ceramic', 'Metal'],
        'milling_speed_rpm': [300.0, 450.0],
        'process_duration_h': [2.0, 5.5],
        'ball_to_powder_ratio': [10.0, 15.0],
        'jar_material': ['Zirconia', 'Steel'],
        'ball_material': ['Zirconia', 'Steel'],
        'material_density_g_cm3': [3.9, 7.8],
        'youngs_modulus_gpa': [350.0, 200.0],
        'd10_um': [1.2, 2.5],
        'd50_um': [5.0, 10.0],
        'd90_um': [12.0, 25.0]
    }
    return pd.DataFrame(data)


@pytest.fixture
def invalid_columns_dataframe(valid_schema):
    """Create a DataFrame with missing required columns."""
    data = {
        'experiment_id': ['exp_001'],
        'source': ['materials_project'],
        # Missing 'material_type' and others
    }
    return pd.DataFrame(data)


@pytest.fixture
def invalid_values_dataframe(valid_schema):
    """Create a DataFrame with invalid values (e.g., negative duration)."""
    data = {
        'experiment_id': ['exp_001'],
        'source': ['materials_project'],
        'material_type': ['Ceramic'],
        'milling_speed_rpm': [-100.0],  # Invalid: negative
        'process_duration_h': [2.0],
        'ball_to_powder_ratio': [10.0],
        'jar_material': ['Zirconia'],
        'ball_material': ['Zirconia'],
        'material_density_g_cm3': [3.9],
        'youngs_modulus_gpa': [350.0],
        'd10_um': [1.2],
        'd50_um': [5.0],
        'd90_um': [12.0]
    }
    return pd.DataFrame(data)


@pytest.fixture
def invalid_enum_dataframe(valid_schema):
    """Create a DataFrame with invalid enum value for 'source'."""
    data = {
        'experiment_id': ['exp_001'],
        'source': ['unknown_source'],  # Invalid enum
        'material_type': ['Ceramic'],
        'milling_speed_rpm': [300.0],
        'process_duration_h': [2.0],
        'ball_to_powder_ratio': [10.0],
        'jar_material': ['Zirconia'],
        'ball_material': ['Zirconia'],
        'material_density_g_cm3': [3.9],
        'youngs_modulus_gpa': [350.0],
        'd10_um': [1.2],
        'd50_um': [5.0],
        'd90_um': [12.0]
    }
    return pd.DataFrame(data)


def test_load_schema(valid_schema):
    """Test that the schema loads correctly."""
    assert valid_schema is not None
    assert 'required' in valid_schema
    assert 'properties' in valid_schema
    assert 'experiment_id' in valid_schema['properties']


def test_validate_dataframe_valid(valid_schema, valid_dataframe):
    """Test validation with a valid DataFrame."""
    errors = validate_dataframe(valid_dataframe, valid_schema)
    assert len(errors) == 0


def test_validate_dataframe_missing_columns(valid_schema, invalid_columns_dataframe):
    """Test validation with missing required columns."""
    errors = validate_dataframe(invalid_columns_dataframe, valid_schema)
    assert len(errors) > 0
    assert any("Missing required columns" in err for err in errors)


def test_validate_dataframe_negative_values(valid_schema, invalid_values_dataframe):
    """Test validation with negative numeric values."""
    errors = validate_dataframe(invalid_values_dataframe, valid_schema)
    assert len(errors) > 0
    assert any("negative values" in err for err in errors)


def test_validate_dataframe_invalid_enum(valid_schema, invalid_enum_dataframe):
    """Test validation with invalid enum value."""
    errors = validate_dataframe(invalid_enum_dataframe, valid_schema)
    assert len(errors) > 0
    assert any("invalid values" in err for err in errors)


def test_validate_and_raise_valid(valid_schema, valid_dataframe):
    """Test that validate_and_raise does not raise for valid data."""
    try:
        validate_and_raise(valid_dataframe, valid_schema)
    except ValueError:
        pytest.fail("validate_and_raise raised ValueError unexpectedly")


def test_validate_and_raise_invalid(valid_schema, invalid_columns_dataframe):
    """Test that validate_and_raise raises ValueError for invalid data."""
    with pytest.raises(ValueError):
        validate_and_raise(invalid_columns_dataframe, valid_schema)


def test_validate_csv_file(tmp_path, valid_dataframe):
    """Test validation of a CSV file."""
    csv_path = tmp_path / "test_data.csv"
    valid_dataframe.to_csv(csv_path, index=False)
    
    assert validate_csv_file(csv_path) is True


def test_validate_csv_file_invalid(tmp_path, invalid_columns_dataframe):
    """Test validation of an invalid CSV file."""
    csv_path = tmp_path / "invalid_data.csv"
    invalid_columns_dataframe.to_csv(csv_path, index=False)
    
    assert validate_csv_file(csv_path) is False


def test_validate_csv_file_not_found():
    """Test validation of a non-existent file."""
    with pytest.raises(FileNotFoundError):
        validate_csv_file("non_existent_file.csv")