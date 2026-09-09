"""
Unit tests for ingestion.py (T012).

Tests schema validation and data loading logic.
"""
import pytest
import pandas as pd
import tempfile
import os
from ingestion import DataSchemaError, validate_schema, load_data_from_hf

class TestDataSchemaError:
    def test_error_message(self):
        """Verify the exact error message for DataSchemaError."""
        try:
            raise DataSchemaError("Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design.")
        except DataSchemaError as e:
            assert "Required columns [recommended_categories, enrolled_categories] missing" in str(e)

class TestValidateSchema:
    def test_valid_schema(self):
        """Test validation with required columns present."""
        df = pd.DataFrame({
            'user_id': [1, 2],
            'recommended_categories': [['A'], ['B']],
            'enrolled_categories': [['C'], ['D']]
        })
        # Should not raise
        result = validate_schema(df)
        assert result is True

    def test_missing_recommended_column(self):
        """Test validation fails when recommended_categories is missing."""
        df = pd.DataFrame({
            'user_id': [1, 2],
            'enrolled_categories': [['C'], ['D']]
        })
        with pytest.raises(DataSchemaError) as exc_info:
            validate_schema(df)
        assert "Required columns [recommended_categories, enrolled_categories] missing" in str(exc_info.value)

    def test_missing_enrolled_column(self):
        """Test validation fails when enrolled_categories is missing."""
        df = pd.DataFrame({
            'user_id': [1, 2],
            'recommended_categories': [['A'], ['B']]
        })
        with pytest.raises(DataSchemaError) as exc_info:
            validate_schema(df)
        assert "Required columns [recommended_categories, enrolled_categories] missing" in str(exc_info.value)

    def test_missing_both_columns(self):
        """Test validation fails when both columns are missing."""
        df = pd.DataFrame({
            'user_id': [1, 2],
            'other_col': [10, 20]
        })
        with pytest.raises(DataSchemaError) as exc_info:
            validate_schema(df)
        assert "Required columns [recommended_categories, enrolled_categories] missing" in str(exc_info.value)

class TestLoadDataFromHF:
    def test_load_data_structure(self):
        """Test that load_data_from_hf returns a DataFrame with expected structure if data exists."""
        # This test assumes the dataset exists on HF.
        # If the dataset is missing, it should raise an error (loud failure).
        # We wrap in try/except to handle the case where the dataset might not be available in CI.
        try:
            df = load_data_from_hf()
            assert isinstance(df, pd.DataFrame)
            assert 'recommended_categories' in df.columns
            assert 'enrolled_categories' in df.columns
        except Exception as e:
            # If the dataset is not found or fetch fails, the test should fail loudly
            # to indicate the real source is unreachable.
            pytest.fail(f"Real data source unavailable: {e}")
