"""
Unit tests for collinearity check functionality.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from analysis.collinearity_check import calculate_collinearity, write_summary_to_csv


class TestCalculateCollinearity:
    """Tests for calculate_collinearity function."""
    
    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data (r=1.0)."""
        df = pd.DataFrame({
            "prompt_token_count": [10, 20, 30, 40, 50],
            "structural_element_count": [1, 2, 3, 4, 5]
        })
        
        results = calculate_collinearity(df)
        
        assert abs(results["correlation_coefficient"]) > 0.999
        assert results["p_value"] < 0.001
        assert results["sample_size"] == 5
        assert results["severity"] == "HIGH"
        
    def test_no_correlation(self):
        """Test with uncorrelated data."""
        np.random.seed(42)
        df = pd.DataFrame({
            "prompt_token_count": np.random.randint(10, 100, 50),
            "structural_element_count": np.random.randint(1, 10, 50)
        })
        
        results = calculate_collinearity(df)
        
        # With random data, correlation should be low (but not exactly 0)
        assert abs(results["correlation_coefficient"]) < 0.3
        assert results["sample_size"] == 50
        
    def test_negative_correlation(self):
        """Test with negatively correlated data."""
        df = pd.DataFrame({
            "prompt_token_count": [50, 40, 30, 20, 10],
            "structural_element_count": [1, 2, 3, 4, 5]
        })
        
        results = calculate_collinearity(df)
        
        assert results["correlation_coefficient"] < -0.99
        assert results["severity"] == "HIGH"
        
    def test_missing_columns(self):
        """Test that missing columns raise ValueError."""
        df = pd.DataFrame({
            "wrong_column": [1, 2, 3]
        })
        
        with pytest.raises(ValueError, match="Column.*not found"):
            calculate_collinearity(df)
            
    def test_insufficient_data(self):
        """Test that insufficient data points raise ValueError."""
        df = pd.DataFrame({
            "prompt_token_count": [10],
            "structural_element_count": [1]
        })
        
        with pytest.raises(ValueError, match="Insufficient data"):
            calculate_collinearity(df)
            
    def test_handles_missing_values(self):
        """Test that NaN values are dropped correctly."""
        df = pd.DataFrame({
            "prompt_token_count": [10, np.nan, 30, 40],
            "structural_element_count": [1, 2, np.nan, 4]
        })
        
        results = calculate_collinearity(df)
        
        # Only 2 complete pairs remain
        assert results["sample_size"] == 2


class TestWriteSummaryToCsv:
    """Tests for write_summary_to_csv function."""
    
    def test_writes_correct_file(self):
        """Test that results are written to CSV correctly."""
        results = {
            "correlation_coefficient": 0.85,
            "p_value": 0.001,
            "sample_size": 100,
            "severity": "HIGH",
            "token_mean": 75.0,
            "token_std": 10.0,
            "struct_mean": 5.0,
            "struct_std": 1.0
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_summary.csv"
            write_summary_to_csv(results, output_path)
            
            assert output_path.exists()
            
            df = pd.read_csv(output_path)
            assert len(df) == 1
            assert df["correlation_coefficient"].iloc[0] == 0.85
            assert df["severity"].iloc[0] == "HIGH"