"""
Unit tests for the data schema validation utilities (code/schema.py).
Validates that schema validation correctly identifies valid and invalid dataframes.
"""
import pandas as pd
import pytest
import yaml
import tempfile
import os

from code.schema import (
    load_schema_from_file,
    validate_column_presence,
    validate_column_types,
    validate_null_values,
    validate_value_ranges,
    validate_categorical_values,
    validate_schema,
    assert_valid_schema,
    filter_valid_records,
    load_schema_and_validate
)


class TestSchemaValidation:
    """Tests for schema.py functionality."""

    def test_validate_column_presence_success(self):
        """Ensure validation passes when all required columns exist."""
        df = pd.DataFrame({"id": [1], "name": ["test"], "score": [90.0]})
        required = ["id", "name", "score"]
        
        result = validate_column_presence(df, required)
        assert result is True

    def test_validate_column_presence_failure(self):
        """Ensure validation fails when a required column is missing."""
        df = pd.DataFrame({"id": [1], "name": ["test"]})
        required = ["id", "name", "missing_col"]
        
        result = validate_column_presence(df, required)
        assert result is False

    def test_validate_column_types_success(self):
        """Ensure validation passes when column types match."""
        df = pd.DataFrame({"id": [1, 2], "score": [90.0, 85.5]})
        types_map = {"id": "int64", "score": "float64"}
        
        result = validate_column_types(df, types_map)
        assert result is True

    def test_validate_column_types_failure(self):
        """Ensure validation fails when column types mismatch."""
        df = pd.DataFrame({"id": [1, 2], "score": ["A", "B"]})
        types_map = {"id": "int64", "score": "float64"}
        
        result = validate_column_types(df, types_map)
        assert result is False

    def test_validate_null_values_success(self):
        """Ensure validation passes when no nulls exist in critical columns."""
        df = pd.DataFrame({"id": [1, 2], "score": [90.0, 85.5]})
        critical = ["id", "score"]
        
        result = validate_null_values(df, critical)
        assert result is True

    def test_validate_null_values_failure(self):
        """Ensure validation fails when nulls exist in critical columns."""
        df = pd.DataFrame({"id": [1, None], "score": [90.0, 85.5]})
        critical = ["id"]
        
        result = validate_null_values(df, critical)
        assert result is False

    def test_validate_value_ranges_success(self):
        """Ensure validation passes when values are within range."""
        df = pd.DataFrame({"score": [50.0, 80.0, 90.0]})
        ranges = {"score": {"min": 0.0, "max": 100.0}}
        
        result = validate_value_ranges(df, ranges)
        assert result is True

    def test_validate_value_ranges_failure(self):
        """Ensure validation fails when values are out of range."""
        df = pd.DataFrame({"score": [50.0, 150.0, 90.0]})
        ranges = {"score": {"min": 0.0, "max": 100.0}}
        
        result = validate_value_ranges(df, ranges)
        assert result is False

    def test_validate_categorical_values_success(self):
        """Ensure validation passes when categorical values are allowed."""
        df = pd.DataFrame({"group": ["Immediate", "Delayed", "Immediate"]})
        categories = {"group": ["Immediate", "Delayed", "Variable"]}
        
        result = validate_categorical_values(df, categories)
        assert result is True

    def test_validate_categorical_values_failure(self):
        """Ensure validation fails when categorical values are not allowed."""
        df = pd.DataFrame({"group": ["Immediate", "Unknown", "Variable"]})
        categories = {"group": ["Immediate", "Delayed", "Variable"]}
        
        result = validate_categorical_values(df, categories)
        assert result is False

    def test_validate_schema_full(self):
        """End-to-end test of validate_schema with a valid schema dict."""
        schema_def = {
            "required_columns": ["id", "value"],
            "types": {"id": "int64", "value": "float64"},
            "critical_columns": ["id"],
            "value_ranges": {"value": {"min": 0.0, "max": 100.0}},
            "categorical_values": {"status": ["active", "inactive"]}
        }
        df = pd.DataFrame({
            "id": [1, 2, 3], 
            "value": [10.0, 20.0, 30.0],
            "status": ["active", "inactive", "active"]
        })
        
        result = validate_schema(df, schema_def)
        assert result is True

    def test_validate_schema_failure_missing_col(self):
        """Ensure validate_schema fails when required column is missing."""
        schema_def = {
            "required_columns": ["id", "missing"],
            "types": {"id": "int64"}
        }
        df = pd.DataFrame({"id": [1, 2]})
        
        result = validate_schema(df, schema_def)
        assert result is False

    def test_validate_schema_failure_null_critical(self):
        """Ensure validate_schema fails when critical column has nulls."""
        schema_def = {
            "required_columns": ["id", "value"],
            "critical_columns": ["id"]
        }
        df = pd.DataFrame({"id": [1, None], "value": [10.0, 20.0]})
        
        result = validate_schema(df, schema_def)
        assert result is False

    def test_assert_valid_schema_success(self):
        """Ensure assert_valid_schema does not raise for valid data."""
        schema_def = {
            "required_columns": ["id"],
            "critical_columns": ["id"]
        }
        df = pd.DataFrame({"id": [1, 2, 3]})
        
        # Should not raise
        assert_valid_schema(df, schema_def)

    def test_assert_valid_schema_failure(self):
        """Ensure assert_valid_schema raises ValueError for invalid data."""
        schema_def = {
            "required_columns": ["id", "missing"],
            "critical_columns": ["id"]
        }
        df = pd.DataFrame({"id": [1, None]})
        
        with pytest.raises(ValueError):
            assert_valid_schema(df, schema_def)

    def test_filter_valid_records(self):
        """Ensure filter_valid_records removes invalid rows."""
        schema_def = {
            "critical_columns": ["id"],
            "value_ranges": {"score": {"min": 0, "max": 100}}
        }
        df = pd.DataFrame({
            "id": [1, None, 3, 4],
            "score": [50.0, 60.0, 150.0, 80.0]
        })
        
        filtered = filter_valid_records(df, schema_def)
        assert len(filtered) == 2
        assert list(filtered["id"]) == [1, 4]

    def test_load_schema_and_validate(self):
        """End-to-end test loading schema from file and validating."""
        schema_def = {
            "version": "1.0",
            "input": {
                "test_data": {
                    "required_columns": ["id", "value"],
                    "types": {"id": "int64", "value": "float64"},
                    "critical_columns": ["id"]
                }
            }
        }
        
        df = pd.DataFrame({"id": [1, 2], "value": [10.0, 20.0]})
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(schema_def, f)
            temp_path = f.name
        
        try:
            result = load_schema_and_validate(temp_path, "input", "test_data", df)
            assert result is True
        finally:
            os.unlink(temp_path)
    
    def test_load_schema_and_validate_failure(self):
        """Ensure load_schema_and_validate returns False on invalid data."""
        schema_def = {
            "version": "1.0",
            "input": {
                "test_data": {
                    "required_columns": ["id", "value", "missing"],
                    "types": {"id": "int64", "value": "float64"},
                    "critical_columns": ["id"]
                }
            }
        }
        
        df = pd.DataFrame({"id": [1, 2], "value": [10.0, 20.0]})
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(schema_def, f)
            temp_path = f.name
        
        try:
            result = load_schema_and_validate(temp_path, "input", "test_data", df)
            assert result is False
        finally:
            os.unlink(temp_path)
    
    def test_load_schema_file_not_found(self):
        """Ensure FileNotFoundError is raised for missing schema file."""
        with pytest.raises(FileNotFoundError):
            load_schema_from_file("/nonexistent/path/schema.yaml")
    
    def test_get_schema_definition_missing_type(self):
        """Ensure KeyError is raised for missing artifact type."""
        schema = {"input": {"test": {}}}
        with pytest.raises(KeyError):
            get_schema_definition(schema, "output", "test")
    
    def test_get_schema_definition_missing_name(self):
        """Ensure KeyError is raised for missing artifact name."""
        schema = {"input": {"test": {}}}
        with pytest.raises(KeyError):
            get_schema_definition(schema, "input", "missing")
