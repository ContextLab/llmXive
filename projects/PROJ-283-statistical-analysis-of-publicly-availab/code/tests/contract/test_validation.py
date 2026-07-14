"""
Contract tests for the validation module.

These tests verify that the validation logic correctly identifies
valid and invalid DataFrames against the defined schemas.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import yaml

from src.validation.validate_contracts import (
    validate_dataframe,
    ValidationResult,
    assert_valid,
)


class TestValidationModule:
    """Tests for the validation module."""

    def _create_temp_schema(self, schema_dict: dict) -> str:
        """Create a temporary YAML schema file."""
        fd, path = tempfile.mkstemp(suffix='.yaml')
        with open(fd, 'w') as f:
            yaml.dump(schema_dict, f)
        return path

    def test_validate_empty_dataframe_with_required_columns(self):
        """Test validation of an empty DataFrame with required columns."""
        schema = {
            'columns': {
                'game_id': {'type': 'string', 'required': True},
                'outcome': {'type': 'string', 'required': True},
            }
        }
        
        df = pd.DataFrame(columns=['game_id', 'outcome'])
        schema_path = self._create_temp_schema(schema)
        
        try:
            result = validate_dataframe(df, schema_path)
            assert result.valid, "Empty DataFrame with correct columns should be valid"
            assert len(result.errors) == 0
        finally:
            Path(schema_path).unlink()

    def test_validate_missing_required_columns(self):
        """Test validation fails when required columns are missing."""
        schema = {
            'columns': {
                'game_id': {'type': 'string', 'required': True},
                'outcome': {'type': 'string', 'required': True},
                'rating': {'type': 'integer', 'required': True},
            }
        }
        
        df = pd.DataFrame({'game_id': ['123'], 'outcome': ['1-0']})
        schema_path = self._create_temp_schema(schema)
        
        try:
            result = validate_dataframe(df, schema_path)
            assert not result.valid
            assert any('Missing required columns' in err for err in result.errors)
            assert 'rating' in result.errors[0]
        finally:
            Path(schema_path).unlink()

    def test_validate_type_mismatch(self):
        """Test validation fails when column types don't match."""
        schema = {
            'columns': {
                'game_id': {'type': 'integer'},
            }
        }
        
        df = pd.DataFrame({'game_id': ['abc']})
        schema_path = self._create_temp_schema(schema)
        
        try:
            result = validate_dataframe(df, schema_path)
            assert not result.valid
            assert any('expected type' in err for err in result.errors)
        finally:
            Path(schema_path).unlink()

    def test_validate_required_null_values(self):
        """Test validation fails when required column has nulls."""
        schema = {
            'columns': {
                'game_id': {'type': 'string', 'required': True},
            }
        }
        
        df = pd.DataFrame({'game_id': ['123', None, '456']})
        schema_path = self._create_temp_schema(schema)
        
        try:
            result = validate_dataframe(df, schema_path)
            assert not result.valid
            assert any('required but contains' in err for err in result.errors)
        finally:
            Path(schema_path).unlink()

    def test_validate_numeric_range_violation(self):
        """Test validation fails when numeric values are out of range."""
        schema = {
            'columns': {
                'rating': {'type': 'integer', 'min': 100, 'max': 3000},
            }
        }
        
        df = pd.DataFrame({'rating': [1500, 50, 2500]})
        schema_path = self._create_temp_schema(schema)
        
        try:
            result = validate_dataframe(df, schema_path)
            assert not result.valid
            assert any('below minimum' in err for err in result.errors)
        finally:
            Path(schema_path).unlink()

    def test_validate_allowed_values_violation(self):
        """Test validation fails when values are not in allowed set."""
        schema = {
            'columns': {
                'outcome': {'type': 'string', 'allowed_values': ['1-0', '0-1', '1/2-1/2']},
            }
        }
        
        df = pd.DataFrame({'outcome': ['1-0', '0-1', 'invalid']})
        schema_path = self._create_temp_schema(schema)
        
        try:
            result = validate_dataframe(df, schema_path)
            assert not result.valid
            assert any('not in allowed set' in err for err in result.errors)
        finally:
            Path(schema_path).unlink()

    def test_validate_unique_constraint(self):
        """Test validation fails when unique constraint is violated."""
        schema = {
            'columns': {
                'game_id': {'type': 'string', 'unique': True},
            }
        }
        
        df = pd.DataFrame({'game_id': ['123', '456', '123']})
        schema_path = self._create_temp_schema(schema)
        
        try:
            result = validate_dataframe(df, schema_path)
            assert not result.valid
            assert any('marked as unique but contains' in err for err in result.errors)
        finally:
            Path(schema_path).unlink()

    def test_assert_valid_raises_on_failure(self):
        """Test that assert_valid raises AssertionError on invalid data."""
        schema = {
            'columns': {
                'game_id': {'type': 'string', 'required': True},
            }
        }
        
        df = pd.DataFrame()  # Missing required column
        schema_path = self._create_temp_schema(schema)
        
        try:
            with pytest.raises(AssertionError):
                assert_valid(df, schema_path, 'test_schema')
        finally:
            Path(schema_path).unlink()

    def test_valid_dataframe_passes_all_checks(self):
        """Test that a valid DataFrame passes all validation checks."""
        schema = {
            'columns': {
                'game_id': {'type': 'string', 'required': True, 'unique': True},
                'rating': {'type': 'integer', 'min': 100, 'max': 3000},
                'outcome': {'type': 'string', 'allowed_values': ['1-0', '0-1', '1/2-1/2']},
            }
        }
        
        df = pd.DataFrame({
            'game_id': ['123', '456', '789'],
            'rating': [1500, 2000, 2500],
            'outcome': ['1-0', '0-1', '1/2-1/2']
        })
        schema_path = self._create_temp_schema(schema)
        
        try:
            result = validate_dataframe(df, schema_path)
            assert result.valid
            assert len(result.errors) == 0
            assert result.df_shape == (3, 3)
        finally:
            Path(schema_path).unlink()
