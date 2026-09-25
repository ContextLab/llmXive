import pytest
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import tempfile
import os

from ingestion import DataSchemaError, validate_schema, ingest_and_clean, ingest_and_save

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

class TestIngestionSchemaValidation:
    """Tests for schema validation logic."""

    def test_validate_schema_passes(self):
        """Test that validation passes when required columns are present."""
        df = pd.DataFrame({
            'recommended_categories': [['Math', 'Science'], ['History']],
            'enrolled_categories': [['Math'], ['History']]
        })
        # Should not raise
        validate_schema(df)

    def test_validate_schema_fails_missing_columns(self):
        """Test that validation raises DataSchemaError with exact message."""
        df = pd.DataFrame({
            'other_col': [1, 2]
        })
        with pytest.raises(DataSchemaError) as exc_info:
            validate_schema(df)
        
        expected_msg = "Required columns ['recommended_categories', 'enrolled_categories'] missing. Dataset does not support the specified experimental design."
        assert str(exc_info.value) == expected_msg

    def test_validate_schema_fails_partial_columns(self):
        """Test that validation raises DataSchemaError if only one column is missing."""
        df = pd.DataFrame({
            'recommended_categories': [['Math']],
            'other_col': [1]
        })
        with pytest.raises(DataSchemaError) as exc_info:
            validate_schema(df)
        
        assert "enrolled_categories" in str(exc_info.value)

class TestIngestionEmptyEnrollments:
    """Tests for empty enrollment handling."""

    def test_ingest_excludes_empty_list_enrollments(self, caplog):
        """Test that rows with empty list enrollments are excluded."""
        df = pd.DataFrame({
            'user_id': ['u1', 'u2', 'u3'],
            'session_id': ['s1', 's2', 's3'],
            'recommended_categories': [['A'], ['B'], ['C']],
            'enrolled_categories': [['A'], [], ['C']]
        })
        
        with caplog.at_level(logging.WARNING):
            result = ingest_and_clean(df)
        
        assert len(result) == 2
        assert 'Excluded' in caplog.text

    def test_ingest_excludes_empty_string_enrollments(self, caplog):
        """Test that rows with empty string enrollments are excluded."""
        df = pd.DataFrame({
            'user_id': ['u1', 'u2'],
            'session_id': ['s1', 's2'],
            'recommended_categories': [['A'], ['B']],
            'enrolled_categories': ['', 'B']
        })
        
        with caplog.at_level(logging.WARNING):
            result = ingest_and_clean(df)
        
        assert len(result) == 1
        assert result.iloc[0]['user_id'] == 'u2'

    def test_ingest_excludes_bracket_empty_enrollments(self, caplog):
        """Test that rows with '[]' string enrollments are excluded."""
        df = pd.DataFrame({
            'user_id': ['u1'],
            'session_id': ['s1'],
            'recommended_categories': [['A']],
            'enrolled_categories': ['[]']
        })
        
        with caplog.at_level(logging.WARNING):
            result = ingest_and_clean(df)
        
        assert len(result) == 0

    def test_ingest_generates_missing_ids(self):
        """Test that missing user_id and session_id are generated."""
        df = pd.DataFrame({
            'recommended_categories': [['A'], ['B']],
            'enrolled_categories': [['A'], ['B']]
        })
        
        result = ingest_and_clean(df)
        
        assert 'user_id' in result.columns
        assert 'session_id' in result.columns
        assert len(result['user_id'].unique()) == 2

    def test_ingest_output_schema(self):
        """Test that output has correct schema columns."""
        df = pd.DataFrame({
            'user_id': ['u1'],
            'session_id': ['s1'],
            'recommended_categories': [['A']],
            'enrolled_categories': [['A']]
        })
        
        result = ingest_and_clean(df)
        
        expected_cols = ['user_id', 'session_id', 'recommended_categories', 'enrolled_categories', 'is_valid']
        assert list(result.columns) == expected_cols
        assert result['is_valid'].iloc[0] is True

class TestIngestionSave:
    """Tests for saving cleaned data."""

    def test_ingest_and_save_creates_parquet(self):
        """Test that ingest_and_save creates a valid Parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_csv = Path(tmpdir) / "input.csv"
            output_parquet = Path(tmpdir) / "output.parquet"
            
            df = pd.DataFrame({
                'user_id': ['u1', 'u2'],
                'session_id': ['s1', 's2'],
                'recommended_categories': [['A'], ['B']],
                'enrolled_categories': [['A'], ['B']]
            })
            df.to_csv(input_csv, index=False)
            
            ingest_and_save(input_csv, output_parquet)
            
            assert output_parquet.exists()
            
            # Verify content
            loaded = pd.read_parquet(output_parquet)
            assert len(loaded) == 2
            assert 'is_valid' in loaded.columns

    def test_ingest_and_save_excludes_empty(self):
        """Test that ingest_and_save excludes empty enrollments before saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_csv = Path(tmpdir) / "input.csv"
            output_parquet = Path(tmpdir) / "output.parquet"
            
            df = pd.DataFrame({
                'user_id': ['u1', 'u2', 'u3'],
                'session_id': ['s1', 's2', 's3'],
                'recommended_categories': [['A'], ['B'], ['C']],
                'enrolled_categories': [['A'], [], ['C']]
            })
            df.to_csv(input_csv, index=False)
            
            ingest_and_save(input_csv, output_parquet)
            
            loaded = pd.read_parquet(output_parquet)
            assert len(loaded) == 2
            assert 'u2' not in loaded['user_id'].values