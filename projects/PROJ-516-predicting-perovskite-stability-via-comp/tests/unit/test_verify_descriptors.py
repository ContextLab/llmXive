"""
Unit tests for verify_descriptors.py
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, mock_open
import io

from code.verify_descriptors import verify_column_presence, verify_column_data_validity

class TestVerifyColumnPresence:
    def test_column_present(self):
        df = pd.DataFrame({"col1": [1, 2], "first_ionization_energy": [5.0, 6.0]})
        is_present, error = verify_column_presence(df, "first_ionization_energy")
        assert is_present is True
        assert error is None

    def test_column_missing(self):
        df = pd.DataFrame({"col1": [1, 2], "col2": [3.0, 4.0]})
        is_present, error = verify_column_presence(df, "first_ionization_energy")
        assert is_present is False
        assert "FR-002 Violation" in error
        assert "first_ionization_energy" in error

class TestVerifyColumnDataValidity:
    def test_valid_numeric_data(self):
        df = pd.DataFrame({"first_ionization_energy": [5.1, 6.2, 7.3]})
        is_valid, error = verify_column_data_validity(df, "first_ionization_energy")
        assert is_valid is True
        assert error is None

    def test_null_values_present(self):
        df = pd.DataFrame({"first_ionization_energy": [5.1, np.nan, 7.3]})
        is_valid, error = verify_column_data_validity(df, "first_ionization_energy")
        assert is_valid is False
        assert "null values" in error

    def test_non_numeric_data(self):
        df = pd.DataFrame({"first_ionization_energy": ["high", "low", "medium"]})
        is_valid, error = verify_column_data_validity(df, "first_ionization_energy")
        assert is_valid is False
        assert "non-numeric" in error

    def test_column_missing(self):
        df = pd.DataFrame({"other_col": [1, 2]})
        is_valid, error = verify_column_data_validity(df, "first_ionization_energy")
        assert is_valid is False
        assert "does not exist" in error

class TestMainExecution:
    @patch("code.verify_descriptors.DESCRIPTORS_PATH")
    @patch("pandas.read_csv")
    @patch("code.verify_descriptors.logger")
    def test_main_success(self, mock_logger, mock_read_csv, mock_path):
        # Mock file exists
        mock_path.exists.return_value = True
        # Mock DataFrame with required column
        mock_df = pd.DataFrame({
            "formula": ["CsPbI3"],
            "first_ionization_energy": [3.89]
        })
        mock_read_csv.return_value = mock_df

        from code.verify_descriptors import main
        result = main()

        assert result == 0
        mock_logger.info.assert_any_call("FR-002 Verification PASSED: 'first_ionization_energy' column is present and valid.")

    @patch("code.verify_descriptors.DESCRIPTORS_PATH")
    @patch("pandas.read_csv")
    @patch("code.verify_descriptors.logger")
    def test_main_missing_column(self, mock_logger, mock_read_csv, mock_path):
        mock_path.exists.return_value = True
        mock_df = pd.DataFrame({"formula": ["CsPbI3"]}) # Missing required col
        mock_read_csv.return_value = mock_df

        from code.verify_descriptors import main
        result = main()

        assert result == 1
        mock_logger.error.assert_called()