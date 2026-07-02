"""
Unit tests for collinearity check (FR-013).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add code/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from analysis.collinearity_check import compute_correlation, write_summary

class TestComputeCorrelation:
    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data."""
        df = pd.DataFrame({
            "token_count": [10, 20, 30, 40, 50],
            "structural_element_count": [1, 2, 3, 4, 5]
        })
        result = compute_correlation(df)
        
        assert result["status"] == "computed"
        assert abs(result["correlation"] - 1.0) < 1e-6
        assert result["p_value"] == 0.0
        assert result["n_samples"] == 5

    def test_perfect_negative_correlation(self):
        """Test with perfectly negatively correlated data."""
        df = pd.DataFrame({
            "token_count": [50, 40, 30, 20, 10],
            "structural_element_count": [1, 2, 3, 4, 5]
        })
        result = compute_correlation(df)
        
        assert result["status"] == "computed"
        assert abs(result["correlation"] - (-1.0)) < 1e-6
        assert result["p_value"] == 0.0
        assert result["n_samples"] == 5

    def test_no_correlation(self):
        """Test with uncorrelated data."""
        df = pd.DataFrame({
            "token_count": [10, 20, 30, 40, 50],
            "structural_element_count": [5, 1, 3, 2, 4]  # Random order
        })
        result = compute_correlation(df)
        
        assert result["status"] == "computed"
        # Correlation should be low but not necessarily zero
        assert abs(result["correlation"]) < 0.5
        assert result["n_samples"] == 5

    def test_insufficient_data(self):
        """Test with less than 2 samples."""
        df = pd.DataFrame({
            "token_count": [10],
            "structural_element_count": [1]
        })
        result = compute_correlation(df)
        
        assert result["status"] == "insufficient_data"
        assert result["correlation"] is None
        assert result["p_value"] is None
        assert result["n_samples"] == 1

    def test_missing_columns(self):
        """Test with missing required columns."""
        df = pd.DataFrame({
            "token_count": [10, 20, 30]
        })
        
        with pytest.raises(ValueError, match="DataFrame must contain"):
            compute_correlation(df)

    def test_handles_missing_values(self):
        """Test that NaN values are dropped."""
        df = pd.DataFrame({
            "token_count": [10, 20, np.nan, 40, 50],
            "structural_element_count": [1, np.nan, 3, 4, 5]
        })
        result = compute_correlation(df)
        
        assert result["status"] == "computed"
        assert result["n_samples"] == 3  # Only 3 complete pairs

class TestWriteSummary:
    def test_creates_file_if_not_exists(self, tmp_path):
        """Test that function creates file if it doesn't exist."""
        output_path = tmp_path / "test_summary.csv"
        results = {
            "correlation": 0.85,
            "p_value": 0.001,
            "n_samples": 100,
            "status": "computed"
        }
        
        write_summary(results, output_path)
        
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 1
        assert df.iloc[0]["correlation_coefficient"] == 0.85
        assert "timestamp" in df.columns

    def test_appends_to_existing_file(self, tmp_path):
        """Test that function appends to existing file."""
        output_path = tmp_path / "test_summary.csv"
        
        # Create initial file
        output_path.write_text("metric,correlation_coefficient\nexisting,0.5\n")
        
        results = {
            "correlation": 0.85,
            "p_value": 0.001,
            "n_samples": 100,
            "status": "computed"
        }
        
        write_summary(results, output_path)
        
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert df.iloc[1]["correlation_coefficient"] == 0.85