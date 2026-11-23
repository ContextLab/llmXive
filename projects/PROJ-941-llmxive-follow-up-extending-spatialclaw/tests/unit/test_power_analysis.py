"""
Unit tests for Power Analysis & Budget Validation (T035b).
"""
import pytest
import json
import os
import math
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from stats.power_analysis import (
    calculate_sample_size,
    validate_budget,
    run_power_analysis,
    DEFAULT_BETA,
    DEFAULT_ALPHA,
    DEFAULT_EFFECT_SIZE,
    DEFAULT_TIME_PER_SAMPLE_MS,
    BUDGET_MS
)
from scipy.stats import norm

class TestCalculateSampleSize:
    def test_sample_size_calculation(self):
        """Test that sample size is calculated correctly for medium effect size."""
        # Expected: N = 2 * ((1.96 + 0.84) / 0.5)^2 ≈ 2 * (5.6)^2 ≈ 62.72 -> 63
        n = calculate_sample_size(0.5)
        assert n >= 60 and n <= 70, f"Expected N around 63, got {n}"

    def test_small_effect_size_increases_n(self):
        """Smaller effect size should require larger N."""
        n_medium = calculate_sample_size(0.5)
        n_small = calculate_sample_size(0.2)
        assert n_small > n_medium

    def test_large_effect_size_decreases_n(self):
        """Larger effect size should require smaller N."""
        n_medium = calculate_sample_size(0.5)
        n_large = calculate_sample_size(0.8)
        assert n_large < n_medium

class TestValidateBudget:
    def test_budget_fits(self):
        """Test validation when N fits within budget."""
        # Budget is 300s (300,000ms). Time per sample 5000ms -> Max N = 60.
        # If we ask for N=10, it should fit.
        result = validate_budget(10, 5000)
        assert result["fits_budget"] is True
        assert result["final_n"] == 10
        assert result["recommendation"] == "Proceed"

    def test_budget_exceeded(self):
        """Test validation when N exceeds budget."""
        # If we ask for N=100, and max is 60, it should reduce.
        result = validate_budget(100, 5000)
        assert result["fits_budget"] is False
        assert result["final_n"] == 60  # 300000 / 5000
        assert result["action_taken"].startswith("Reduced N")
        assert "warning" in result

    def test_budget_insufficient(self):
        """Test when budget is too small for even minimal N=5."""
        # Time per sample 70,000ms -> Max N = 4.
        result = validate_budget(5, 70000)
        assert result["fits_budget"] is False
        assert result["final_n"] == 0
        assert "Budget Insufficient" in result["recommendation"]

class TestRunPowerAnalysis:
    @patch('stats.power_analysis.os.makedirs')
    @patch('stats.power_analysis.open')
    @patch('stats.power_analysis.json.dump')
    def test_report_generation(self, mock_dump, mock_open, mock_makedirs):
        """Test that the report is generated and written correctly."""
        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        report = run_power_analysis("data/test_report.json")
        
        assert "results" in report
        assert "n_samples_calculated" in report["results"]
        assert "fits_budget" in report["results"]
        assert "final_n" in report["results"]
        
        # Verify file write was called
        mock_open.assert_called_once()
        mock_dump.assert_called_once()