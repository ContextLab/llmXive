"""
Tests for the data validation gate (T009).
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

from code.validate_data import validate_data


class TestValidateData:
    """Test cases for the validate_data function."""

    def test_missing_input_file(self, tmp_path):
        """Test that validation fails when input file is missing."""
        non_existent_file = tmp_path / "non_existent.csv"
        result = validate_data(non_existent_file)

        assert result["status"] == "FAIL"
        assert result["has_experimental_data"] is False
        assert "not found" in result["error"]
        assert result["sc001_validity"] == "FAIL"

    def test_missing_lambda_max_exp_column(self, tmp_path):
        """Test validation when lambda_max_exp column is missing."""
        # Create a CSV without lambda_max_exp
        test_data = {
            "smi": ["CCO", "CCCO"],
            "other_column": [1.0, 2.0]
        }
        input_file = tmp_path / "test_missing_col.csv"
        pd.DataFrame(test_data).to_csv(input_file, index=False)

        result = validate_data(input_file)

        assert result["status"] == "FAIL"
        assert result["has_experimental_data"] is False
        assert "lambda_max_exp" in result["missing_columns"]
        assert result["sc001_validity"] == "FAIL"

    def test_empty_lambda_max_exp_column(self, tmp_path):
        """Test validation when lambda_max_exp column exists but has no values."""
        test_data = {
            "smi": ["CCO", "CCCO"],
            "lambda_max_exp": [None, None]
        }
        input_file = tmp_path / "test_empty_col.csv"
        pd.DataFrame(test_data).to_csv(input_file, index=False)

        result = validate_data(input_file)

        assert result["status"] == "FAIL"
        assert result["has_experimental_data"] is False
        assert result["sc001_validity"] == "FAIL"

    def test_valid_experimental_data(self, tmp_path):
        """Test validation with valid experimental data."""
        test_data = {
            "smi": ["CCO", "CCCO", "CCCCO"],
            "lambda_max_exp": [254.5, 260.0, 265.2]
        }
        input_file = tmp_path / "test_valid.csv"
        pd.DataFrame(test_data).to_csv(input_file, index=False)

        result = validate_data(input_file)

        assert result["status"] == "PASS"
        assert result["has_experimental_data"] is True
        assert result["sc001_validity"] == "PASS"
        assert "column_stats" in result
        assert result["column_stats"]["count"] == 3
        assert abs(result["column_stats"]["mean"] - 259.9) < 0.1

    def test_mixed_null_and_valid_data(self, tmp_path):
        """Test validation with some null values but valid data present."""
        test_data = {
            "smi": ["CCO", "CCCO", "CCCCO", "CCCCCO"],
            "lambda_max_exp": [254.5, None, 265.2, 270.1]
        }
        input_file = tmp_path / "test_mixed.csv"
        pd.DataFrame(test_data).to_csv(input_file, index=False)

        result = validate_data(input_file)

        assert result["status"] == "PASS"
        assert result["has_experimental_data"] is True
        assert result["sc001_validity"] == "PASS"
        assert result["column_stats"]["count"] == 3  # Only non-null values

    def test_computed_only_dataset(self, tmp_path):
        """Test validation for dataset with only computed lambda_max values."""
        # Simulate a dataset with only computed values
        test_data = {
            "smi": ["CCO", "CCCO"],
            "lambda_max_calc": [255.0, 261.0]
        }
        input_file = tmp_path / "test_computed.csv"
        pd.DataFrame(test_data).to_csv(input_file, index=False)

        result = validate_data(input_file)

        assert result["status"] == "FAIL"
        assert result["has_experimental_data"] is False
        assert result["sc001_validity"] == "FAIL"
        assert "lambda_max_exp" in result["missing_columns"]

    def test_large_dataset_chunked_loading(self, tmp_path):
        """Test that large datasets are handled correctly (chunked loading)."""
        # Create a larger dataset to trigger chunked loading logic
        n_rows = 150000
        test_data = {
            "smi": [f"C{i}" for i in range(n_rows)],
            "lambda_max_exp": [250.0 + (i % 100) for i in range(n_rows)]
        }
        input_file = tmp_path / "test_large.csv"
        pd.DataFrame(test_data).to_csv(input_file, index=False)

        result = validate_data(input_file)

        assert result["status"] == "PASS"
        assert result["has_experimental_data"] is True
        assert result["total_rows"] == n_rows
        assert result["column_stats"]["count"] == n_rows