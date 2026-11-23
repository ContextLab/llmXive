"""
Unit tests for the power analysis module.
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.analysis.power_analysis import (
    calculate_effect_size_f,
    estimate_required_n,
    run_power_analysis
)

class TestPowerAnalysis:
    
    def test_calculate_effect_size_f(self):
        """Test Cohen's f calculation."""
        mean_diff = 0.1
        std_dev = 0.25
        # f = (mean_diff / sqrt(2)) / std_dev
        expected = (0.1 / 1.4142) / 0.25
        result = calculate_effect_size_f(mean_diff, std_dev)
        assert abs(result - expected) < 1e-4

    def test_calculate_effect_size_f_zero_std(self):
        """Test that zero std dev returns 0."""
        result = calculate_effect_size_f(0.1, 0.0)
        assert result == 0.0

    def test_estimate_required_n(self):
        """Test N estimation for medium effect."""
        # For f=0.25, lambda approx 9.63 -> N = 9.63 / 0.0625 = 154
        n = estimate_required_n(0.25)
        assert n > 100
        assert n < 200

    def test_run_power_analysis_structure(self):
        """Test that the report dictionary has the expected structure."""
        report = run_power_analysis()
        
        assert "analysis_type" in report
        assert "study_design" in report
        assert "parameters" in report
        assert "sample_size_analysis" in report
        assert "justification" in report
        
        assert report["sample_size_analysis"]["proposed_total_n"] == 500
        assert report["sample_size_analysis"]["is_sufficient"] is True
        
    def test_report_generation(self):
        """Test that the report is generated with correct content."""
        # We can't easily test the file I/O in a pure unit test without temp files,
        # but we can verify the logic returns the correct state.
        report = run_power_analysis()
        assert "N=500" in report["justification"]
        assert "sufficient" in report["justification"]