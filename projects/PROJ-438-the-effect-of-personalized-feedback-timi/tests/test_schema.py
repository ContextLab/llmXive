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
    validate_schema
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

    def test_validate_schema_full(self):
        """End-to-end test of validate_schema with a valid schema dict."""
        schema_def = {
            "required_columns": ["id", "value"],
            "types": {"id": "int64", "value": "float64"},
            "critical_columns": ["id"]
        }
        df = pd.DataFrame({"id": [1, 2], "value": [10.0, 20.0]})
        
        result = validate_schema(df, schema_def)
        assert result is True
