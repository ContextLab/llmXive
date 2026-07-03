"""
Unit tests for T020: Collinearity Check.

Tests the correlation calculation logic between token count and structural element count.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import csv

from analysis.collinearity_check import calculate_collinearity, write_summary_to_csv


class TestCalculateCollinearity:
    """Tests for the calculate_collinearity function."""

    def test_perfect_positive_correlation(self, tmp_path):
        """Test with perfectly correlated data."""
        data = {
            "prompt_token_count": [10, 20, 30, 40, 50],
            "structural_element_count": [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        result = calculate_collinearity(df)
        
        assert result["status"] == "success"
        assert result["sample_size"] == 5
        assert abs(result["correlation"] - 1.0) < 1e-6
        assert result["p_value"] < 0.05  # Significant

    def test_no_correlation(self):
        """Test with uncorrelated data."""
        # Create data where tokens and structure are not correlated
        np.random.seed(42)
        data = {
            "prompt_token_count": np.random.randint(10, 100, 50),
            "structural_element_count": np.random.randint(1, 10, 50)
        }
        df = pd.DataFrame(data)
        
        result = calculate_collinearity(df)
        
        assert result["status"] == "success"
        assert result["sample_size"] == 50
        # Correlation should be close to 0, but not necessarily exactly 0
        assert abs(result["correlation"]) < 0.3

    def test_negative_correlation(self):
        """Test with negatively correlated data."""
        data = {
            "prompt_token_count": [50, 40, 30, 20, 10],
            "structural_element_count": [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        result = calculate_collinearity(df)
        
        assert result["status"] == "success"
        assert abs(result["correlation"] - (-1.0)) < 1e-6

    def test_insufficient_data(self):
        """Test with insufficient data points."""
        data = {
            "prompt_token_count": [10],
            "structural_element_count": [1]
        }
        df = pd.DataFrame(data)
        
        result = calculate_collinearity(df)
        
        assert result["status"] == "insufficient_data"
        assert result["correlation"] is None

    def test_missing_columns(self):
        """Test with missing required columns."""
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Required columns not found"):
            calculate_collinearity(df)

    def test_missing_values_handling(self):
        """Test that rows with NaN are dropped."""
        data = {
            "prompt_token_count": [10, 20, np.nan, 40],
            "structural_element_count": [1, np.nan, 3, 4]
        }
        df = pd.DataFrame(data)
        
        result = calculate_collinearity(df)
        
        # Only 1 valid pair remains: (10, 1) -> wait, (40, 4) is the only full pair?
        # Actually: (10, 1), (20, NaN), (NaN, 3), (40, 4) -> 2 valid pairs
        # (10, 1) and (40, 4)
        assert result["sample_size"] == 2


class TestWriteSummaryToCSV:
    """Tests for the write_summary_to_csv function."""

    def test_writes_correct_format(self, tmp_path):
        """Test that the CSV is written with correct headers and values."""
        result = {
            "correlation": 0.85,
            "p_value": 0.001,
            "sample_size": 100,
            "status": "success"
        }
        output_path = tmp_path / "analysis_summary.csv"
        
        write_summary_to_csv(result, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1
        row = rows[0]
        assert row["metric"] == "prompt_token_vs_structural_element_correlation"
        assert float(row["correlation_coefficient"]) == 0.85
        assert float(row["p_value"]) == 0.001
        assert int(row["sample_size"]) == 100
        assert row["status"] == "success"

    def test_appends_to_existing_file(self, tmp_path):
        """Test that new results are appended to existing CSV."""
        # Create initial file
        initial_path = tmp_path / "analysis_summary.csv"
        initial_path.parent.mkdir(parents=True)
        
        # Write first result
        result1 = {"correlation": 0.5, "p_value": 0.05, "sample_size": 50, "status": "success"}
        write_summary_to_csv(result1, initial_path)
        
        # Write second result
        result2 = {"correlation": 0.6, "p_value": 0.04, "sample_size": 60, "status": "success"}
        write_summary_to_csv(result2, initial_path)
        
        with open(initial_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert float(rows[0]["correlation_coefficient"]) == 0.5
        assert float(rows[1]["correlation_coefficient"]) == 0.6
