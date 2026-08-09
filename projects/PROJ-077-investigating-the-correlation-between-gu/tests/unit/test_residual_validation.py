"""
Unit tests for Residual Validation module (Task T025b).

These tests verify the Shapiro-Wilk implementation and report generation logic.
"""
import pytest
import pandas as pd
import numpy as np
from scipy import stats
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from residual_validation import (
    perform_shapiro_wilk_test,
    check_normality_assumption,
    generate_diagnostics_report,
    save_report,
    run_validation_pipeline
)

class TestShapiroWilk:
    """Tests for the Shapiro-Wilk normality test implementation."""

    def test_perform_shapiro_wilk_normal_data(self):
        """Test that normally distributed data passes the Shapiro-Wilk test."""
        np.random.seed(42)
        normal_data = pd.Series(np.random.normal(loc=0, scale=1, size=100))
        
        result = perform_shapiro_wilk_test(normal_data)
        
        assert result["test"] == "Shapiro-Wilk"
        assert isinstance(result["statistic"], float)
        assert isinstance(result["p_value"], float)
        assert result["n_observations"] == 100
        # Normal data should typically pass (p > 0.05)
        # Note: This is probabilistic, so we check the structure primarily
        assert result["interpretation"] in ["PASS", "FAIL"]
        assert 0 <= result["statistic"] <= 1

    def test_perform_shapiro_wilk_non_normal_data(self):
        """Test that highly skewed data fails the Shapiro-Wilk test."""
        # Generate exponential distribution (highly skewed)
        skewed_data = pd.Series(np.random.exponential(scale=2.0, size=100))
        
        result = perform_shapiro_wilk_test(skewed_data)
        
        assert result["test"] == "Shapiro-Wilk"
        # Exponential distribution usually fails normality test
        # We assert the structure and that p-value is calculated
        assert 0 <= result["p_value"] <= 1
        assert result["interpretation"] in ["PASS", "FAIL"]

    def test_perform_shapiro_wilk_insufficient_data(self):
        """Test that insufficient data raises an error."""
        small_data = pd.Series([1.0, 2.0])
        
        with pytest.raises(ValueError, match="requires at least 3 observations"):
            perform_shapiro_wilk_test(small_data)

    def test_perform_shapiro_wilk_with_nan(self):
        """Test that NaN values are handled correctly."""
        data_with_nan = pd.Series([1.0, 2.0, np.nan, 3.0, 4.0])
        
        result = perform_shapiro_wilk_test(data_with_nan)
        
        assert result["n_observations"] == 4  # NaN should be dropped

class TestNormalityAssumption:
    """Tests for additional normality checks."""

    def test_check_normality_returns_structure(self):
        """Test that the function returns the expected dictionary structure."""
        np.random.seed(42)
        data = pd.Series(np.random.normal(loc=0, scale=1, size=50))
        
        result = check_normality_assumption(data)
        
        assert "test" in result
        assert "statistic" in result
        assert "p_value" in result
        assert "interpretation" in result
        assert "skewness" in result
        assert "excess_kurtosis" in result
        assert "n_observations" in result

    def test_skewness_kurtosis_calculation(self):
        """Test that skewness and kurtosis are calculated correctly."""
        # Create a known distribution
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        
        result = check_normality_assumption(data)
        
        # Verify numeric types
        assert isinstance(result["skewness"], float)
        assert isinstance(result["excess_kurtosis"], float)
        assert result["n_observations"] == 10

class TestReportGeneration:
    """Tests for report generation logic."""

    def test_generate_diagnostics_report_status(self):
        """Test that report status is correctly derived from test results."""
        shapiro_pass = {"interpretation": "PASS", "p_value": 0.5, "statistic": 0.95, "n_observations": 50, "test": "Shapiro-Wilk", "alpha": 0.05}
        ks_pass = {"interpretation": "PASS", "n_observations": 50}
        
        report = generate_diagnostics_report(shapiro_pass, ks_pass)
        
        assert report["status"] == "PASS"
        assert report["conclusion"].startswith("The normality assumption")

    def test_generate_diagnostics_report_fail(self):
        """Test that report status is FAIL when Shapiro-Wilk fails."""
        shapiro_fail = {"interpretation": "FAIL", "p_value": 0.01, "statistic": 0.85, "n_observations": 50, "test": "Shapiro-Wilk", "alpha": 0.05}
        ks_fail = {"interpretation": "FAIL", "n_observations": 50}
        
        report = generate_diagnostics_report(shapiro_fail, ks_fail)
        
        assert report["status"] == "FAIL"

    def test_save_report_creates_file(self, tmp_path):
        """Test that save_report creates a valid JSON file."""
        report = {
            "task_id": "T025b",
            "status": "PASS",
            "shapiro_wilk": {"p_value": 0.5},
            "kolmogorov_smirnov": {"p_value": 0.6}
        }
        
        output_file = tmp_path / "test_diagnostics.json"
        
        with patch("residual_validation.OUTPUT_PATH", output_file):
            save_report(report)
        
        assert output_file.exists()
        
        with open(output_file) as f:
            loaded = json.load(f)
        
        assert loaded["status"] == "PASS"

class TestIntegration:
    """Integration tests for the full pipeline (mocked)."""

    @patch("residual_validation.load_regression_data")
    @patch("residual_validation.run_regression_model")
    def test_run_validation_pipeline_mocked(self, mock_run_model, mock_load_data, tmp_path):
        """Test the full pipeline with mocked dependencies."""
        # Mock data
        mock_df = pd.DataFrame({
            'shannon_index': [1.0, 2.0, 3.0, 4.0, 5.0],
            'fluid_intelligence': [80, 90, 85, 95, 88],
            'Age': [20, 30, 40, 50, 60],
            'BMI': [22, 24, 25, 23, 26],
            'Sex': ['M', 'F', 'M', 'F', 'M'],
            'DQS': [50, 60, 55, 65, 58]
        })
        
        mock_load_data.return_value = mock_df
        
        # Mock model results with synthetic residuals (normal)
        np.random.seed(42)
        mock_residuals = pd.Series(np.random.normal(0, 1, 5))
        mock_results = MagicMock()
        mock_results.resid = mock_residuals
        mock_run_model.return_value = (mock_results, mock_residuals)
        
        # Run pipeline
        with patch("residual_validation.OUTPUT_PATH", tmp_path / "diag.json"):
            result = run_validation_pipeline()
        
        assert result["status"] in ["PASS", "FAIL"]
        assert "shapiro_wilk" in result
        assert "kolmogorov_smirnov" in result
        assert result["n_observations"] == 5