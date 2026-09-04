import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

from code.data.validate_raw import (
    validate_raw_data_variables,
    validate_raw_directory,
    REQUIRED_VARIABLES
)


class TestValidateRawVariables:
    """Tests for validate_raw_data_variables function."""

    def test_all_variables_present(self, tmp_path):
        """Test that a file with all required variables passes."""
        file_path = tmp_path / "valid_data.csv"
        df = pd.DataFrame({
            "avatar_condition": [0, 1],
            "pre_self_esteem": [10.0, 12.0],
            "post_self_esteem": [11.0, 13.0],
            "comparison_tendency": [0.5, 0.8]
        })
        df.to_csv(file_path, index=False)

        assert validate_raw_data_variables(file_path) is True

    def test_missing_variable(self, tmp_path):
        """Test that a file missing a required variable fails."""
        file_path = tmp_path / "missing_var.csv"
        df = pd.DataFrame({
            "avatar_condition": [0, 1],
            "pre_self_esteem": [10.0, 12.0],
            "post_self_esteem": [11.0, 13.0]
            # missing "comparison_tendency"
        })
        df.to_csv(file_path, index=False)

        assert validate_raw_data_variables(file_path) is False

    def test_extra_variables_ok(self, tmp_path):
        """Test that extra columns do not cause failure."""
        file_path = tmp_path / "extra_cols.csv"
        df = pd.DataFrame({
            "avatar_condition": [0, 1],
            "pre_self_esteem": [10.0, 12.0],
            "post_self_esteem": [11.0, 13.0],
            "comparison_tendency": [0.5, 0.8],
            "extra_column": [1, 2]
        })
        df.to_csv(file_path, index=False)

        assert validate_raw_data_variables(file_path) is True

    def test_empty_file_raises(self, tmp_path):
        """Test that an empty CSV raises ValueError."""
        file_path = tmp_path / "empty.csv"
        file_path.write_text("")  # Empty file
        
        with pytest.raises(ValueError):
            validate_raw_data_variables(file_path)

    def test_file_not_found_raises(self, tmp_path):
        """Test that a non-existent file raises FileNotFoundError."""
        file_path = tmp_path / "non_existent.csv"
        
        with pytest.raises(FileNotFoundError):
            validate_raw_data_variables(file_path)


class TestValidateRawDirectory:
    """Tests for validate_raw_directory function."""

    def test_directory_with_valid_csv(self, tmp_path):
        """Test directory containing a valid CSV."""
        csv_path = tmp_path / "valid.csv"
        df = pd.DataFrame({
            "avatar_condition": [0, 1],
            "pre_self_esteem": [10.0, 12.0],
            "post_self_esteem": [11.0, 13.0],
            "comparison_tendency": [0.5, 0.8]
        })
        df.to_csv(csv_path, index=False)

        assert validate_raw_directory(tmp_path) is True

    def test_directory_with_only_invalid_csv(self, tmp_path):
        """Test directory containing only invalid CSVs."""
        csv_path = tmp_path / "invalid.csv"
        df = pd.DataFrame({
            "avatar_condition": [0, 1],
            "pre_self_esteem": [10.0, 12.0]
            # Missing others
        })
        df.to_csv(csv_path, index=False)

        assert validate_raw_directory(tmp_path) is False

    def test_directory_empty(self, tmp_path):
        """Test directory with no CSV files."""
        assert validate_raw_directory(tmp_path) is False

    def test_directory_non_existent(self, tmp_path):
        """Test behavior when directory itself doesn't exist."""
        non_existent = tmp_path / "does_not_exist"
        assert validate_raw_directory(non_existent) is False
