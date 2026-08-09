"""
Contract tests for the ingestion module schema validation.

These tests ensure that the ingestion module correctly validates
the required schema and handles missing columns appropriately.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from ingestion.validator import validate_schema, REQUIRED_COLUMNS
from ingestion.fetcher import DataFetchError

class TestIngestionSchema:
    """Tests for schema validation logic."""
    
    def test_validate_schema_passes_with_all_columns(self):
        """Test that validation passes when all required columns are present."""
        df = pd.DataFrame({
            'age': [65, 70, 75],
            'stimulus_type': ['nostalgia', 'control', 'nostalgia'],
            'perseverative_errors': [10, 15, 12],
            'categories_completed': [5, 4, 6]
        })
        
        is_valid, missing = validate_schema(df)
        
        assert is_valid is True
        assert len(missing) == 0
    
    def test_validate_schema_fails_missing_age(self):
        """Test that validation fails when 'age' column is missing."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia', 'control'],
            'perseverative_errors': [10, 15],
            'categories_completed': [5, 4]
        })
        
        is_valid, missing = validate_schema(df)
        
        assert is_valid is False
        assert 'age' in missing
    
    def test_validate_schema_fails_missing_scores(self):
        """Test that validation fails when score columns are missing."""
        df = pd.DataFrame({
            'age': [65, 70],
            'stimulus_type': ['nostalgia', 'control']
        })
        
        is_valid, missing = validate_schema(df)
        
        assert is_valid is False
        assert 'perseverative_errors' in missing
        assert 'categories_completed' in missing
    
    def test_validate_schema_fails_multiple_missing(self):
        """Test that validation reports all missing columns."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia']
        })
        
        is_valid, missing = validate_schema(df)
        
        assert is_valid is False
        assert len(missing) == 3
        assert set(missing) == set(['age', 'perseverative_errors', 'categories_completed'])
    
    def test_validate_schema_with_optional_columns(self):
        """Test that optional columns do not affect validation."""
        df = pd.DataFrame({
            'age': [65],
            'stimulus_type': ['nostalgia'],
            'perseverative_errors': [10],
            'categories_completed': [5],
            'MMSE': [28],
            'participant_id': ['P0001']
        })
        
        is_valid, missing = validate_schema(df)
        
        assert is_valid is True
        assert len(missing) == 0
    
    def test_validate_schema_with_null_values(self):
        """Test that schema validation passes even with null values (filtering happens later)."""
        df = pd.DataFrame({
            'age': [65, None, 70],
            'stimulus_type': ['nostalgia', 'control', None],
            'perseverative_errors': [10, 15, None],
            'categories_completed': [5, None, 6]
        })
        
        # Schema validation only checks column presence, not nulls
        is_valid, missing = validate_schema(df)
        
        assert is_valid is True
        assert len(missing) == 0
    
    def test_validate_schema_empty_dataframe(self):
        """Test that an empty dataframe with correct columns passes schema validation."""
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        
        is_valid, missing = validate_schema(df)
        
        assert is_valid is True
        assert len(missing) == 0
    
    def test_validate_schema_extra_columns_ignored(self):
        """Test that extra columns are ignored during schema validation."""
        df = pd.DataFrame({
            'age': [65],
            'stimulus_type': ['nostalgia'],
            'perseverative_errors': [10],
            'categories_completed': [5],
            'extra_col': ['test']
        })
        
        is_valid, missing = validate_schema(df)
        
        assert is_valid is True
        assert len(missing) == 0