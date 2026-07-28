"""
Unit tests for schema validation logic.

These tests verify that the validate_schema function correctly:
1. Validates required fields are present
2. Validates no null values in required fields
3. Handles missing schema files gracefully
4. Raises appropriate exceptions for invalid data
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
import yaml

from src.utils.exceptions import InsufficientDataError, SchemaValidationError
from src.preprocess.validate_schema import validate_schema, load_schema, validate_file


@pytest.fixture
def sample_schema():
    """Create a temporary schema file for testing."""
    schema = {
        "fields": {
            "experiment_id": {"type": "str", "required": True},
            "source": {"type": "str", "required": True},
            "material_type": {"type": "str", "required": True},
            "milling_speed": {"type": "float", "required": True},
            "milling_time": {"type": "float", "required": True},
            "ball_to_powder_ratio": {"type": "float", "required": True},
            "youngs_modulus": {"type": "float", "required": True},
            "density": {"type": "float", "required": True},
            "d10": {"type": "float", "required": True},
            "d50": {"type": "float", "required": True},
            "d90": {"type": "float", "required": True},
            "process_duration": {"type": "float", "required": True}
        }
    }
    return schema

@pytest.fixture
def valid_dataframe():
    """Create a valid DataFrame for testing."""
    data = {
        "experiment_id": ["exp1", "exp2"],
        "source": ["materials_project", "nist"],
        "material_type": ["steel", "aluminum"],
        "milling_speed": [500.0, 600.0],
        "milling_time": [2.0, 3.0],
        "ball_to_powder_ratio": [10.0, 15.0],
        "youngs_modulus": [200.0, 70.0],
        "density": [7.8, 2.7],
        "d10": [10.5, 12.3],
        "d50": [25.0, 30.5],
        "d90": [45.0, 55.0],
        "process_duration": [2.5, 3.5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def small_dataframe():
    """Create a small valid DataFrame (for testing row count independence)."""
    data = {
        "experiment_id": ["exp1"],
        "source": ["materials_project"],
        "material_type": ["steel"],
        "milling_speed": [500.0],
        "milling_time": [2.0],
        "ball_to_powder_ratio": [10.0],
        "youngs_modulus": [200.0],
        "density": [7.8],
        "d10": [10.5],
        "d50": [25.0],
        "d90": [45.0],
        "process_duration": [2.5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def invalid_nulls_dataframe():
    """Create a DataFrame with null values in required fields."""
    data = {
        "experiment_id": ["exp1", None],
        "source": ["materials_project", "nist"],
        "material_type": ["steel", "aluminum"],
        "milling_speed": [500.0, 600.0],
        "milling_time": [2.0, 3.0],
        "ball_to_powder_ratio": [10.0, 15.0],
        "youngs_modulus": [200.0, 70.0],
        "density": [7.8, 2.7],
        "d10": [10.5, 12.3],
        "d50": [25.0, 30.5],
        "d90": [45.0, 55.0],
        "process_duration": [2.5, 3.5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def missing_column_dataframe():
    """Create a DataFrame missing a required column."""
    data = {
        "experiment_id": ["exp1", "exp2"],
        "source": ["materials_project", "nist"],
        "material_type": ["steel", "aluminum"],
        "milling_speed": [500.0, 600.0],
        "milling_time": [2.0, 3.0],
        "ball_to_powder_ratio": [10.0, 15.0],
        "youngs_modulus": [200.0, 70.0],
        "density": [7.8, 2.7],
        "d10": [10.5, 12.3],
        "d50": [25.0, 30.5],
        "d90": [45.0, 55.0]
        # Missing process_duration
    }
    return pd.DataFrame(data)

def test_validate_schema_success(valid_dataframe, sample_schema):
    """Test that valid data passes schema validation."""
    result = validate_schema(valid_dataframe, sample_schema)
    assert result is not None
    assert len(result) == 2
    assert "experiment_id" in result.columns

def test_validate_schema_insufficient_rows(small_dataframe, sample_schema):
    """Test that small datasets (even 1 row) pass schema validation (row count is not checked)."""
    # This test verifies that schema validation does NOT check row count
    result = validate_schema(small_dataframe, sample_schema)
    assert result is not None
    assert len(result) == 1  # Should pass even with only 1 row

def test_validate_schema_null_values(invalid_nulls_dataframe, sample_schema):
    """Test that null values in required fields raise InsufficientDataError."""
    with pytest.raises(InsufficientDataError) as exc_info:
        validate_schema(invalid_nulls_dataframe, sample_schema)
    
    assert "null" in str(exc_info.value).lower() or "null" in str(exc_info.value)

def test_validate_schema_missing_column(missing_column_dataframe, sample_schema):
    """Test that missing required columns raise InsufficientDataError."""
    with pytest.raises(InsufficientDataError) as exc_info:
        validate_schema(missing_column_dataframe, sample_schema)
    
    assert "missing" in str(exc_info.value).lower()
    assert "process_duration" in str(exc_info.value)

def test_validate_schema_none_input(sample_schema):
    """Test that None input raises SchemaValidationError."""
    with pytest.raises(SchemaValidationError):
        validate_schema(None, sample_schema)

def test_validate_schema_non_dataframe(sample_schema):
    """Test that non-DataFrame input raises SchemaValidationError."""
    with pytest.raises(SchemaValidationError):
        validate_schema("not a dataframe", sample_schema)

def test_load_schema_file_not_found():
    """Test that missing schema file falls back to default schema."""
    with patch('pathlib.Path.exists', return_value=False):
        schema = load_schema("nonexistent/path.yaml")
        assert schema is not None
        assert "fields" in schema

def test_load_schema_success(tmp_path, sample_schema):
    """Test successful loading of schema from file."""
    schema_file = tmp_path / "test_schema.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(sample_schema, f)
    
    result = load_schema(str(schema_file))
    assert result == sample_schema

def test_validate_file_parquet(tmp_path, valid_dataframe):
    """Test validation of a Parquet file."""
    parquet_file = tmp_path / "test.parquet"
    valid_dataframe.to_parquet(parquet_file)
    
    result = validate_file(str(parquet_file))
    assert result is not None
    assert len(result) == 2

def test_validate_file_csv(tmp_path, valid_dataframe):
    """Test validation of a CSV file."""
    csv_file = tmp_path / "test.csv"
    valid_dataframe.to_csv(csv_file, index=False)
    
    result = validate_file(str(csv_file))
    assert result is not None
    assert len(result) == 2

def test_validate_file_not_found():
    """Test that missing file raises SchemaValidationError."""
    with pytest.raises(SchemaValidationError):
        validate_file("nonexistent/file.parquet")

def test_validate_file_unsupported_format(tmp_path):
    """Test that unsupported file format raises SchemaValidationError."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("some text")
    
    with pytest.raises(SchemaValidationError):
        validate_file(str(txt_file))
