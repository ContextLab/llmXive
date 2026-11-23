"""
Unit tests for the schema validation logic in src/preprocess/validate_schema.py.
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
import yaml

from src.utils.exceptions import InsufficientDataError, SchemaValidationError
from src.preprocess.validate_schema import load_schema, validate_schema, validate_file


@pytest.fixture
def sample_schema():
    """Return a sample schema dictionary for testing."""
    return {
        "version": "1.0",
        "description": "Test schema",
        "fields": [
            {"name": "experiment_id", "type": "string", "required": True},
            {"name": "source", "type": "string", "required": True},
            {"name": "material_type", "type": "string", "required": True},
            {"name": "milling_speed", "type": "float", "required": True},
            {"name": "milling_time", "type": "float", "required": True},
            {"name": "ball_to_powder_ratio", "type": "float", "required": True},
            {"name": "youngs_modulus", "type": "float", "required": True},
            {"name": "density", "type": "float", "required": True},
            {"name": "d10", "type": "float", "required": True},
            {"name": "d50", "type": "float", "required": True},
            {"name": "d90", "type": "float", "required": True},
            {"name": "process_duration", "type": "float", "required": True},
        ]
    }


@pytest.fixture
def valid_dataframe(sample_schema):
    """Return a valid DataFrame matching the schema."""
    return pd.DataFrame({
        "experiment_id": ["exp_001", "exp_002"],
        "source": ["NIST", "Materials Project"],
        "material_type": ["Steel", "Aluminum"],
        "milling_speed": [300.0, 400.0],
        "milling_time": [2.0, 4.0],
        "ball_to_powder_ratio": [10.0, 15.0],
        "youngs_modulus": [200.0, 70.0],
        "density": [7.8, 2.7],
        "d10": [10.0, 15.0],
        "d50": [25.0, 30.0],
        "d90": [50.0, 60.0],
        "process_duration": [2.0, 4.0],
    })


@pytest.fixture
def small_dataframe(sample_schema):
    """Return a small valid DataFrame (1 row) - T007b does NOT check row count."""
    return pd.DataFrame({
        "experiment_id": ["exp_001"],
        "source": ["NIST"],
        "material_type": ["Steel"],
        "milling_speed": [300.0],
        "milling_time": [2.0],
        "ball_to_powder_ratio": [10.0],
        "youngs_modulus": [200.0],
        "density": [7.8],
        "d10": [10.0],
        "d50": [25.0],
        "d90": [50.0],
        "process_duration": [2.0],
    })


@pytest.fixture
def invalid_nulls_dataframe(sample_schema):
    """Return a DataFrame with null values in a required column."""
    df = valid_dataframe(sample_schema).copy()
    df.loc[0, "d50"] = None
    return df


@pytest.fixture
def missing_column_dataframe(sample_schema):
    """Return a DataFrame missing a required column."""
    df = valid_dataframe(sample_schema).copy()
    df = df.drop(columns=["d90"])
    return df


def test_validate_schema_success(valid_dataframe, sample_schema):
    """Test that a valid DataFrame passes validation."""
    result = validate_schema(valid_dataframe, sample_schema)
    assert result is not None
    assert len(result) == 2
    assert list(result.columns) == list(valid_dataframe.columns)


def test_validate_schema_insufficient_rows(small_dataframe, sample_schema):
    """
    Test that a DataFrame with < 150 rows PASSES validation.
    T007b explicitly states: 'This task does NOT check row count;
    row count validation is handled later in T015c and T017c.'
    """
    # This should NOT raise an error
    result = validate_schema(small_dataframe, sample_schema)
    assert result is not None
    assert len(result) == 1


def test_validate_schema_null_values(invalid_nulls_dataframe, sample_schema):
    """Test that a DataFrame with nulls raises InsufficientDataError."""
    with pytest.raises(InsufficientDataError) as exc_info:
        validate_schema(invalid_nulls_dataframe, sample_schema)
    assert "null values" in str(exc_info.value).lower()


def test_validate_schema_missing_column(missing_column_dataframe, sample_schema):
    """Test that a DataFrame with missing columns raises InsufficientDataError."""
    with pytest.raises(InsufficientDataError) as exc_info:
        validate_schema(missing_column_dataframe, sample_schema)
    assert "Missing required columns" in str(exc_info.value)


def test_validate_schema_none_input():
    """Test that passing None raises SchemaValidationError."""
    with pytest.raises(SchemaValidationError):
        validate_schema(None)


def test_validate_schema_non_dataframe():
    """Test that passing a non-DataFrame raises SchemaValidationError."""
    with pytest.raises(SchemaValidationError):
        validate_schema({"key": "value"})


def test_load_schema_file_not_found():
    """Test that loading a non-existent schema file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_schema("/path/to/non_existent_schema.yaml")


def test_load_schema_success(tmp_path):
    """Test loading a valid schema file."""
    schema_content = {
        "version": "1.0",
        "fields": [
            {"name": "id", "type": "string", "required": True}
        ]
    }
    schema_file = tmp_path / "schema.yaml"
    with open(schema_file, "w") as f:
        yaml.dump(schema_content, f)

    loaded = load_schema(str(schema_file))
    assert loaded["version"] == "1.0"
    assert len(loaded["fields"]) == 1


def test_validate_file_parquet(valid_dataframe, sample_schema, tmp_path):
    """Test validating a parquet file."""
    file_path = tmp_path / "test.parquet"
    valid_dataframe.to_parquet(file_path)
    result = validate_file(str(file_path), sample_schema)
    assert len(result) == 2


def test_validate_file_csv(valid_dataframe, sample_schema, tmp_path):
    """Test validating a csv file."""
    file_path = tmp_path / "test.csv"
    valid_dataframe.to_csv(file_path, index=False)
    result = validate_file(str(file_path), sample_schema)
    assert len(result) == 2


def test_validate_file_not_found():
    """Test that validating a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        validate_file("/path/to/non_existent_file.csv")


def test_validate_file_unsupported_format(valid_dataframe, tmp_path):
    """Test that an unsupported file format raises ValueError."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("some text")
    with pytest.raises(ValueError) as exc_info:
        validate_file(str(file_path))
    assert "Unsupported file format" in str(exc_info.value)
