"""
Unit tests for schema validation functionality.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import tempfile
import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.utils.validation import (
    load_schema,
    validate_field_type,
    validate_enum,
    validate_range,
    validate_dataframe_against_schema,
    validate_dataset
)


class TestSchemaValidation:
    """Test suite for schema validation functions."""

    @pytest.fixture
    def sample_schema(self):
        """Create a sample schema for testing."""
        return {
            "name": "test_schema",
            "version": "1.0.0",
            "required_fields": ["id", "name", "age", "score"],
            "fields": {
                "id": {
                    "type": "str",
                    "nullable": False
                },
                "name": {
                    "type": "str",
                    "nullable": False
                },
                "age": {
                    "type": "int",
                    "nullable": False,
                    "min": 0,
                    "max": 150
                },
                "score": {
                    "type": "float",
                    "nullable": True,
                    "min": 0.0,
                    "max": 100.0
                },
                "category": {
                    "type": "str",
                    "nullable": True,
                    "enum": ["A", "B", "C"]
                },
                "active": {
                    "type": "bool",
                    "nullable": False
                }
            }
        }

    @pytest.fixture
    def valid_dataframe(self):
        """Create a valid DataFrame for testing."""
        return pd.DataFrame({
            "id": ["ID001", "ID002", "ID003"],
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "score": [85.5, 90.0, 78.3],
            "category": ["A", "B", "C"],
            "active": [True, False, True]
        })

    @pytest.fixture
    def invalid_dataframe(self):
        """Create an invalid DataFrame for testing."""
        return pd.DataFrame({
            "id": ["ID001", "ID002", None],  # Null in non-nullable field
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, -5, 35],  # Negative age out of range
            "score": [85.5, 150.0, 78.3],  # Score out of range
            "category": ["A", "D", "C"],  # Invalid enum value
            "active": [True, False, "yes"]  # Invalid type for bool
        })

    def test_load_schema_valid(self, sample_schema, tmp_path):
        """Test loading a valid schema file."""
        schema_file = tmp_path / "test_schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(sample_schema, f)

        loaded_schema = load_schema(schema_file)
        assert loaded_schema == sample_schema

    def test_load_schema_not_found(self):
        """Test loading a non-existent schema file."""
        with pytest.raises(FileNotFoundError):
            load_schema("/nonexistent/path/schema.yaml")

    def test_load_schema_invalid_format(self, tmp_path):
        """Test loading a schema with invalid format."""
        schema_file = tmp_path / "invalid_schema.yaml"
        with open(schema_file, 'w') as f:
            f.write("not a valid schema structure")

        schema = yaml.safe_load(f)
        with pytest.raises(ValueError):
            load_schema(schema_file)

    def test_validate_field_type_int(self):
        """Test integer type validation."""
        assert validate_field_type(25, "int") is True
        assert validate_field_type(25.0, "int") is False  # Float is not int
        assert validate_field_type("25", "int") is False
        assert validate_field_type(True, "int") is False  # Bool is not int
        assert pd.isna(validate_field_type(np.nan, "int"))  # NaN handling

    def test_validate_field_type_float(self):
        """Test float type validation."""
        assert validate_field_type(25.5, "float") is True
        assert validate_field_type(25, "float") is True  # Int is valid float
        assert validate_field_type("25.5", "float") is False
        assert validate_field_type(True, "float") is False

    def test_validate_field_type_str(self):
        """Test string type validation."""
        assert validate_field_type("hello", "str") is True
        assert validate_field_type(123, "str") is False
        assert validate_field_type(True, "str") is False

    def test_validate_field_type_bool(self):
        """Test boolean type validation."""
        assert validate_field_type(True, "bool") is True
        assert validate_field_type(False, "bool") is True
        assert validate_field_type(1, "bool") is False
        assert validate_field_type("true", "bool") is False

    def test_validate_enum_valid(self):
        """Test enum validation with valid values."""
        assert validate_enum("A", ["A", "B", "C"]) is True
        assert validate_enum("a", ["A", "B", "C"]) is True  # Case insensitive
        assert validate_enum("B", ["A", "B", "C"]) is True

    def test_validate_enum_invalid(self):
        """Test enum validation with invalid values."""
        assert validate_enum("D", ["A", "B", "C"]) is False
        assert validate_enum("d", ["A", "B", "C"]) is False

    def test_validate_range_valid(self):
        """Test range validation with valid values."""
        assert validate_range(50, 0, 100) is True
        assert validate_range(0, 0, 100) is True
        assert validate_range(100, 0, 100) is True
        assert validate_range(50, None, 100) is True
        assert validate_range(50, 0, None) is True

    def test_validate_range_invalid(self):
        """Test range validation with invalid values."""
        assert validate_range(-1, 0, 100) is False
        assert validate_range(101, 0, 100) is False
        assert validate_range("50", 0, 100) is False

    def test_validate_dataframe_valid(self, valid_dataframe, sample_schema):
        """Test validation of a valid DataFrame."""
        errors = validate_dataframe_against_schema(valid_dataframe, sample_schema)
        assert len(errors) == 0

    def test_validate_dataframe_missing_required_field(self, sample_schema):
        """Test validation with missing required field."""
        df = pd.DataFrame({
            "id": ["ID001"],
            "name": ["Alice"],
            "age": [25]
            # Missing "score" which is required
        })
        errors = validate_dataframe_against_schema(df, sample_schema)
        assert any("score" in error for error in errors)

    def test_validate_dataframe_type_mismatch(self, sample_schema):
        """Test validation with type mismatch."""
        df = pd.DataFrame({
            "id": [123],  # Should be str
            "name": ["Alice"],
            "age": [25],
            "score": [85.5],
            "category": ["A"],
            "active": [True]
        })
        errors = validate_dataframe_against_schema(df, sample_schema)
        assert any("id" in error and "type" in error for error in errors)

    def test_validate_dataframe_out_of_range(self, sample_schema):
        """Test validation with out-of-range values."""
        df = pd.DataFrame({
            "id": ["ID001"],
            "name": ["Alice"],
            "age": [200],  # Out of range
            "score": [85.5],
            "category": ["A"],
            "active": [True]
        })
        errors = validate_dataframe_against_schema(df, sample_schema)
        assert any("age" in error for error in errors)

    def test_validate_dataframe_invalid_enum(self, sample_schema):
        """Test validation with invalid enum value."""
        df = pd.DataFrame({
            "id": ["ID001"],
            "name": ["Alice"],
            "age": [25],
            "score": [85.5],
            "category": ["D"],  # Invalid enum
            "active": [True]
        })
        errors = validate_dataframe_against_schema(df, sample_schema)
        assert any("category" in error for error in errors)

    def test_validate_dataset_integration(self, sample_schema, valid_dataframe, tmp_path):
        """Test full dataset validation workflow."""
        # Create temporary schema and data files
        schema_file = tmp_path / "test_schema.yaml"
        data_file = tmp_path / "test_data.csv"

        with open(schema_file, 'w') as f:
            yaml.dump(sample_schema, f)

        valid_dataframe.to_csv(data_file, index=False)

        # Validate dataset
        result = validate_dataset(data_file, schema_file)
        assert result is True

    def test_validate_dataset_file_not_found(self, sample_schema, tmp_path):
        """Test validation with missing data file."""
        schema_file = tmp_path / "test_schema.yaml"
        data_file = tmp_path / "nonexistent_data.csv"

        with open(schema_file, 'w') as f:
            yaml.dump(sample_schema, f)

        with pytest.raises(FileNotFoundError):
            validate_dataset(data_file, schema_file)

    def test_validate_dataset_invalid_csv(self, sample_schema, tmp_path):
        """Test validation with invalid CSV file."""
        schema_file = tmp_path / "test_schema.yaml"
        data_file = tmp_path / "invalid_data.csv"

        with open(schema_file, 'w') as f:
            yaml.dump(sample_schema, f)

        with open(data_file, 'w') as f:
            f.write("not a valid csv content")

        with pytest.raises(RuntimeError):
            validate_dataset(data_file, schema_file)
