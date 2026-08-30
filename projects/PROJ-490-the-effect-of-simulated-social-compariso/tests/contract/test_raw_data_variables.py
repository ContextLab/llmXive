"""
Contract tests for raw data variable validation (T013).
Ensures that the pipeline fails loudly if required variables are missing.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.data.validate_raw import validate_raw_data_variables, validate_raw_directory, REQUIRED_VARIABLES

class TestRawDataValidation:
    
    def test_all_variables_present(self):
        """Test that validation passes when all required variables are present."""
        df = pd.DataFrame({
            'avatar_condition': [0, 1, 0, 1],
            'pre_self_esteem': [20.5, 22.1, 19.8, 23.4],
            'post_self_esteem': [21.0, 21.5, 20.2, 24.1],
            'comparison_tendency': [3.2, 4.1, 2.8, 3.9],
            'extra_col': [1, 2, 3, 4]
        })
        
        # Should not raise
        result = validate_raw_data_variables(df)
        assert result is True

    def test_missing_one_variable(self):
        """Test that validation fails when one required variable is missing."""
        df = pd.DataFrame({
            'avatar_condition': [0, 1, 0, 1],
            'pre_self_esteem': [20.5, 22.1, 19.8, 23.4],
            'post_self_esteem': [21.0, 21.5, 20.2, 24.1],
            # Missing 'comparison_tendency'
        })
        
        with pytest.raises(ValueError) as excinfo:
            validate_raw_data_variables(df)
        
        assert "comparison_tendency" in str(excinfo.value)

    def test_missing_multiple_variables(self):
        """Test that validation fails when multiple required variables are missing."""
        df = pd.DataFrame({
            'avatar_condition': [0, 1, 0, 1],
            # Missing 'pre_self_esteem', 'post_self_esteem', 'comparison_tendency'
        })
        
        with pytest.raises(ValueError) as excinfo:
            validate_raw_data_variables(df)
        
        missing = {'pre_self_esteem', 'post_self_esteem', 'comparison_tendency'}
        found_in_msg = missing.intersection(set(str(excinfo.value).split()))
        # The error message should list the missing ones
        assert len(found_in_msg) > 0

    def test_empty_dataframe(self):
        """Test that validation fails on empty DataFrame."""
        df = pd.DataFrame(columns=['avatar_condition', 'pre_self_esteem', 'post_self_esteem', 'comparison_tendency'])
        
        with pytest.raises(ValueError) as excinfo:
            validate_raw_data_variables(df)
        
        assert "None or empty" in str(excinfo.value)

    def test_validate_directory_all_pass(self):
        """Test directory validation when all CSVs have required variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid CSV
            df = pd.DataFrame({
                'avatar_condition': [0, 1],
                'pre_self_esteem': [10.0, 11.0],
                'post_self_esteem': [12.0, 13.0],
                'comparison_tendency': [1.0, 2.0]
            })
            csv_path = Path(tmpdir) / "valid_data.csv"
            df.to_csv(csv_path, index=False)
            
            result = validate_raw_directory(tmpdir)
            assert result is True

    def test_validate_directory_one_fails(self):
        """Test directory validation when one CSV is missing variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid CSV
            df_valid = pd.DataFrame({
                'avatar_condition': [0, 1],
                'pre_self_esteem': [10.0, 11.0],
                'post_self_esteem': [12.0, 13.0],
                'comparison_tendency': [1.0, 2.0]
            })
            (Path(tmpdir) / "valid_data.csv").to_csv(df_valid, index=False)
            
            # Create an invalid CSV (missing comparison_tendency)
            df_invalid = pd.DataFrame({
                'avatar_condition': [0, 1],
                'pre_self_esteem': [10.0, 11.0],
                'post_self_esteem': [12.0, 13.0]
            })
            (Path(tmpdir) / "invalid_data.csv").to_csv(df_invalid, index=False)
            
            with pytest.raises(ValueError) as excinfo:
                validate_raw_directory(tmpdir)
            
            assert "comparison_tendency" in str(excinfo.value)

    def test_directory_not_found(self):
        """Test that validation fails if directory does not exist."""
        with pytest.raises(FileNotFoundError):
            validate_raw_directory("/non/existent/path/12345")

    def test_no_csv_files(self):
        """Test that validation fails if directory exists but has no CSVs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a text file, not csv
            Path(tmpdir, "readme.txt").touch()
            
            with pytest.raises(FileNotFoundError):
                validate_raw_directory(tmpdir)