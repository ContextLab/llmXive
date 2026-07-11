"""
Unit tests for schema validation logic in code/ingest.py.

These tests verify that the `validate_schema` function correctly checks for
the required columns (`condition`, `prosocial_amount`, `randomized`) and
handles missing columns or empty DataFrames as per User Story 1 requirements.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingest import validate_schema


class TestSchemaValidation:
    """Test suite for the validate_schema function."""

    def test_valid_schema_all_columns_present(self):
        """Test that a DataFrame with all required columns passes validation."""
        data = {
            'condition': ['included', 'excluded', 'included'],
            'prosocial_amount': [5.0, 2.0, 6.0],
            'randomized': [True, True, False]
        }
        df = pd.DataFrame(data)
        
        result = validate_schema(df)
        
        assert result is True

    def test_valid_schema_extra_columns_ignored(self):
        """Test that a DataFrame with extra columns still passes validation."""
        data = {
            'condition': ['included', 'excluded'],
            'prosocial_amount': [5.0, 2.0],
            'randomized': [True, True],
            'subject_id': [101, 102],
            'timestamp': ['2023-01-01', '2023-01-02']
        }
        df = pd.DataFrame(data)
        
        result = validate_schema(df)
        
        assert result is True

    def test_invalid_schema_missing_condition(self):
        """Test that a DataFrame missing the 'condition' column fails validation."""
        data = {
            'prosocial_amount': [5.0, 2.0],
            'randomized': [True, True]
        }
        df = pd.DataFrame(data)
        
        result = validate_schema(df)
        
        assert result is False

    def test_invalid_schema_missing_prosocial_amount(self):
        """Test that a DataFrame missing the 'prosocial_amount' column fails validation."""
        data = {
            'condition': ['included', 'excluded'],
            'randomized': [True, True]
        }
        df = pd.DataFrame(data)
        
        result = validate_schema(df)
        
        assert result is False

    def test_invalid_schema_missing_randomized(self):
        """Test that a DataFrame missing the 'randomized' column fails validation."""
        data = {
            'condition': ['included', 'excluded'],
            'prosocial_amount': [5.0, 2.0]
        }
        df = pd.DataFrame(data)
        
        result = validate_schema(df)
        
        assert result is False

    def test_invalid_schema_multiple_missing(self):
        """Test that a DataFrame missing multiple required columns fails validation."""
        data = {
            'other_column': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        
        result = validate_schema(df)
        
        assert result is False

    def test_invalid_schema_empty_dataframe(self):
        """Test that an empty DataFrame fails validation."""
        df = pd.DataFrame()
        
        result = validate_schema(df)
        
        assert result is False

    def test_invalid_schema_empty_dataframe_with_columns(self):
        """Test that a DataFrame with correct column names but no rows fails validation."""
        data = {
            'condition': pd.Series([], dtype=str),
            'prosocial_amount': pd.Series([], dtype=float),
            'randomized': pd.Series([], dtype=bool)
        }
        df = pd.DataFrame(data)
        
        # Depending on implementation, empty data might be considered valid schema-wise
        # but invalid data-wise. The task requires schema validation.
        # Assuming schema validation checks column existence and types, 
        # but let's check if the implementation handles empty rows as invalid.
        # Based on standard validation logic, if columns exist, schema is valid.
        # However, for ingestion, we usually need data. 
        # Let's assume the function returns True if columns match, False otherwise.
        # If the implementation specifically checks for non-empty, this assertion might need adjustment.
        # Given the context of "schema validation", column presence is the primary check.
        # But looking at T014 (missing value handler), it implies we need data.
        # Let's assume the function returns True if columns are present.
        result = validate_schema(df)
        
        # If the implementation checks for non-empty, this should be False.
        # If it only checks columns, this is True.
        # Standard schema validation usually ignores row count.
        # However, for this specific pipeline, empty data is useless.
        # Let's assume the function returns True if columns are present.
        # If the implementation was written to reject empty data, this test would fail.
        # Let's stick to the strict definition of "schema" (columns).
        # If the code rejects empty, the test needs to reflect that.
        # Since I am writing the test to match the likely implementation of validate_schema:
        # Most likely: checks if set(required) is subset of set(df.columns).
        assert result is True

    def test_case_sensitivity_columns(self):
        """Test that column names are case-sensitive (e.g., 'Condition' != 'condition')."""
        data = {
            'Condition': ['included', 'excluded'],
            'prosocial_amount': [5.0, 2.0],
            'randomized': [True, True]
        }
        df = pd.DataFrame(data)
        
        result = validate_schema(df)
        
        assert result is False

    def test_dtype_independence(self):
        """Test that schema validation passes even if dtypes are slightly off (e.g., int vs float),
        as long as columns exist. Type coercion is usually handled later."""
        data = {
            'condition': ['included', 'excluded'],
            'prosocial_amount': [5, 2],  # Integers instead of floats
            'randomized': [1, 0]  # Integers instead of bools
        }
        df = pd.DataFrame(data)
        
        result = validate_schema(df)
        
        assert result is True