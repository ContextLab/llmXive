"""
Unit tests for finalize_dataset.py (Task T017)
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

# Import the function to test
from ingestion.finalize_dataset import validate_and_save_merged_dataset
from config import ERR_INSUFFICIENT_DATA


class TestValidateAndSaveMergedDataset:
    """Tests for the validate_and_save_merged_dataset function."""

    def test_valid_dataset_saves_successfully(self, tmp_path):
        """Test that a valid dataset with >= 20 rows is saved successfully."""
        # Create a mock dataframe
        data = {
            'yield_strength_MPa': [200 + i for i in range(25)],
            'shear_modulus_GPa': [80 + i * 0.5 for i in range(25)],
            'composition': ['Fe' for _ in range(25)]
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "merged.csv"
        
        result = validate_and_save_merged_dataset(df, output_path, min_rows=20)
        
        assert result is True
        assert output_path.exists()
        
        # Verify saved content
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == 25
        assert 'yield_strength_MPa' in saved_df.columns

    def test_insufficient_rows_raises_error(self, tmp_path):
        """Test that a dataset with < 20 rows raises ValueError with ERR_INSUFFICIENT_DATA."""
        data = {
            'yield_strength_MPa': [200 + i for i in range(15)],
            'shear_modulus_GPa': [80 + i * 0.5 for i in range(15)],
            'composition': ['Fe' for _ in range(15)]
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "merged.csv"
        
        with pytest.raises(ValueError) as exc_info:
            validate_and_save_merged_dataset(df, output_path, min_rows=20)
        
        assert str(exc_info.value) == ERR_INSUFFICIENT_DATA

    def test_missing_required_columns_raises_error(self, tmp_path):
        """Test that missing required columns raises ValueError."""
        data = {
            'yield_strength_MPa': [200 + i for i in range(25)],
            # Missing 'shear_modulus_GPa'
            'composition': ['Fe' for _ in range(25)]
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "merged.csv"
        
        with pytest.raises(ValueError) as exc_info:
            validate_and_save_merged_dataset(df, output_path, min_rows=20)
        
        assert "Required column 'shear_modulus_GPa' missing" in str(exc_info.value)

    def test_empty_dataframe_raises_error(self, tmp_path):
        """Test that an empty dataframe raises ValueError."""
        df = pd.DataFrame()
        
        output_path = tmp_path / "merged.csv"
        
        with pytest.raises(ValueError) as exc_info:
            validate_and_save_merged_dataset(df, output_path, min_rows=20)
        
        assert "Input dataframe is empty or None" in str(exc_info.value)

    def test_null_values_in_required_columns_filters_and_validates(self, tmp_path):
        """Test that rows with nulls in required columns are filtered and re-validated."""
        # Create 25 rows, but make 10 have nulls in yield_strength
        data = {
            'yield_strength_MPa': [200 + i if i < 15 else None for i in range(25)],
            'shear_modulus_GPa': [80 + i * 0.5 for i in range(25)],
            'composition': ['Fe' for _ in range(25)]
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "merged.csv"
        
        # Should succeed because 15 valid rows >= 20? No, 15 < 20.
        # Let's make 22 valid rows out of 30 total.
        data = {
            'yield_strength_MPa': [200 + i if i < 22 else None for i in range(30)],
            'shear_modulus_GPa': [80 + i * 0.5 for i in range(30)],
            'composition': ['Fe' for _ in range(30)]
        }
        df = pd.DataFrame(data)
        
        result = validate_and_save_merged_dataset(df, output_path, min_rows=20)
        
        assert result is True
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == 22

    def test_null_values_in_required_columns_filters_and_fails(self, tmp_path):
        """Test that if filtering leaves < 20 rows, it raises ERR_INSUFFICIENT_DATA."""
        # 30 rows total, but 15 have nulls -> 15 valid. 15 < 20.
        data = {
            'yield_strength_MPa': [200 + i if i < 15 else None for i in range(30)],
            'shear_modulus_GPa': [80 + i * 0.5 for i in range(30)],
            'composition': ['Fe' for _ in range(30)]
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "merged.csv"
        
        with pytest.raises(ValueError) as exc_info:
            validate_and_save_merged_dataset(df, output_path, min_rows=20)
        
        assert str(exc_info.value) == ERR_INSUFFICIENT_DATA