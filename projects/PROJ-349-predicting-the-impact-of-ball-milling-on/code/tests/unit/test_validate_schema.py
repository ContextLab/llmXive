"""
Unit tests for schema validation logic in validate_schema.py
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
import yaml

from src.exceptions import InsufficientDataError, SchemaValidationError
from src.utils.validate_schema import validate_schema, load_schema, SCHEMA_PATH


@pytest.fixture
def sample_schema():
    """Provide a valid schema dictionary."""
    return {
        "type": "object",
        "required": ["id", "value", "category"],
        "properties": {
            "id": {"type": "string"},
            "value": {"type": "number"},
            "category": {"type": "string"}
        }
    }


@pytest.fixture
def valid_dataframe():
    """Create a DataFrame that meets minimum row count and schema requirements."""
    data = {
        "id": [f"exp_{i}" for i in range(200)],
        "value": [float(i) for i in range(200)],
        "category": ["A"] * 100 + ["B"] * 100
    }
    return pd.DataFrame(data)


@pytest.fixture
def small_dataframe():
    """Create a DataFrame with fewer than 150 rows."""
    data = {
        "id": [f"exp_{i}" for i in range(50)],
        "value": [float(i) for i in range(50)],
        "category": ["A"] * 25 + ["B"] * 25
    }
    return pd.DataFrame(data)


@pytest.fixture
def invalid_nulls_dataframe():
    """Create a DataFrame with null values in required columns."""
    data = {
        "id": [f"exp_{i}" for i in range(200)],
        "value": [float(i) if i % 2 != 0 else None for i in range(200)],
        "category": ["A"] * 100 + ["B"] * 100
    }
    return pd.DataFrame(data)


@pytest.fixture
def missing_column_dataframe():
    """Create a DataFrame missing a required column."""
    data = {
        "id": [f"exp_{i}" for i in range(200)],
        "value": [float(i) for i in range(200)]
    }
    return pd.DataFrame(data)


def test_validate_schema_success(valid_dataframe, sample_schema, tmp_path):
    """Test that validation passes for a valid DataFrame."""
    # Write sample schema to a temporary file
    schema_file = tmp_path / "test_schema.yaml"
    with open(schema_file, "w") as f:
        yaml.dump(sample_schema, f)

    # Mock SCHEMA_PATH to point to our temp file
    with patch("src.utils.validate_schema.SCHEMA_PATH", schema_file):
        result = validate_schema(valid_dataframe)
        assert result is True


def test_validate_schema_insufficient_rows(small_dataframe, sample_schema, tmp_path):
    """Test that InsufficientDataError is raised for < 150 rows."""
    schema_file = tmp_path / "test_schema.yaml"
    with open(schema_file, "w") as f:
        yaml.dump(sample_schema, f)

    with patch("src.utils.validate_schema.SCHEMA_PATH", schema_file):
        with pytest.raises(InsufficientDataError) as exc_info:
            validate_schema(small_dataframe)
        assert "insufficient data" in str(exc_info.value).lower()
        assert "150" in str(exc_info.value)


def test_validate_schema_null_values(invalid_nulls_dataframe, sample_schema, tmp_path):
    """Test that SchemaValidationError is raised for null values in required columns."""
    schema_file = tmp_path / "test_schema.yaml"
    with open(schema_file, "w") as f:
        yaml.dump(sample_schema, f)

    with patch("src.utils.validate_schema.SCHEMA_PATH", schema_file):
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema(invalid_nulls_dataframe)
        assert "null" in str(exc_info.value).lower()


def test_validate_schema_missing_column(missing_column_dataframe, sample_schema, tmp_path):
    """Test that SchemaValidationError is raised for missing required columns."""
    schema_file = tmp_path / "test_schema.yaml"
    with open(schema_file, "w") as f:
        yaml.dump(sample_schema, f)

    with patch("src.utils.validate_schema.SCHEMA_PATH", schema_file):
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema(missing_column_dataframe)
        assert "missing" in str(exc_info.value).lower()


def test_load_schema_file_not_found():
    """Test that FileNotFoundError is raised for missing schema file."""
    with pytest.raises(FileNotFoundError):
        load_schema(Path("/nonexistent/path/schema.yaml"))


def test_load_schema_success(sample_schema, tmp_path):
    """Test successful schema loading."""
    schema_file = tmp_path / "test_schema.yaml"
    with open(schema_file, "w") as f:
        yaml.dump(sample_schema, f)

    loaded = load_schema(schema_file)
    assert loaded == sample_schema