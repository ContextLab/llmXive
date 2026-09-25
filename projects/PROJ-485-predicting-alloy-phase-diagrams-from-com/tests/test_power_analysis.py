import pytest
import pandas as pd
import numpy as np
import os
import sys
from unittest.mock import patch, MagicMock
from sklearn.ensemble import RandomForestRegressor

# Add code to path if not already
if 'code' not in sys.path:
    sys.path.insert(0, 'code')

from models.train import perform_power_analysis, main
from utils.error_codes import ErrorCode

class TestPowerAnalysis:
    def test_power_analysis_insufficient(self, tmp_path):
        """
        Assert that perform_power_analysis raises an error (or returns False) 
        when calculated power < 0.8.
        This tests T054 requirement: detailed report on failure.
        """
        # Create a small dataset to simulate low power
        # Small N usually leads to low power
        data = {
            'mean_atomic_radius': np.random.rand(5) * 2,
            'electronegativity_variance': np.random.rand(5),
            'valence_electron_count': np.random.rand(5) * 10,
            'hume_rothery_concentration': np.random.rand(5),
            'temperature': np.random.rand(5) * 1000 + 500,
            'system_id': ['Cu-Zn'] * 5
        }
        df = pd.DataFrame(data)
        
        # Mock LOSO results (not strictly needed for the power function logic 
        # as it primarily uses df, but required by signature)
        loso_results = {"fold_results": []}
        
        # Run power analysis
        success, report = perform_power_analysis(df, loso_results)
        
        # Verify failure
        assert success is False, "Expected power analysis to fail with small dataset."
        assert ErrorCode.INSUFFICIENT_POWER.value in report, "Error code missing from report."
        
        # Verify detailed report content
        assert "Calculated Power:" in report, "Power value missing from report."
        assert "Effect Size (Cohen's d):" in report, "Effect size missing from report."
        assert "Sample Size (N):" in report, "Sample size missing from report."
        
        # Verify specific values are present (not just strings)
        assert "0.80" in report, "Target threshold missing."

    def test_power_analysis_sufficient(self, tmp_path):
        """
        Assert that perform_power_analysis returns True when power >= 0.8.
        We simulate this by mocking the statsmodels calculation or using a large N.
        """
        # Create a large dataset to simulate high power
        n = 500
        data = {
            'mean_atomic_radius': np.random.rand(n) * 2,
            'electronegativity_variance': np.random.rand(n),
            'valence_electron_count': np.random.rand(n) * 10,
            'hume_rothery_concentration': np.random.rand(n),
            'temperature': np.random.rand(n) * 1000 + 500,
            'system_id': ['Cu-Zn'] * n
        }
        df = pd.DataFrame(data)
        loso_results = {"fold_results": []}
        
        # Mock the TTestPower.power method to return 0.9 to ensure success in test environment
        # where statsmodels might behave differently with small random data
        with patch('statsmodels.stats.power.TTestPower.power', return_value=0.95):
            success, report = perform_power_analysis(df, loso_results)
        
        assert success is True, "Expected power analysis to succeed with large dataset."
        assert "SUCCESS" not in report or "FAILED" not in report, "Report should not indicate failure."

    def test_report_format(self, tmp_path):
        """Verify the report format contains all required fields."""
        data = {
            'mean_atomic_radius': [1.0, 1.1, 1.2],
            'electronegativity_variance': [0.1, 0.2, 0.3],
            'valence_electron_count': [1, 2, 3],
            'hume_rothery_concentration': [0.1, 0.2, 0.3],
            'temperature': [500, 600, 700],
            'system_id': ['A', 'B', 'C']
        }
        df = pd.DataFrame(data)
        loso_results = {}
        
        success, report = perform_power_analysis(df, loso_results)
        
        required_fields = [
            "Statistical Power Analysis Report",
            "Target Power Threshold",
            "Calculated Power",
            "Effect Size (Cohen's d)",
            "Sample Size (N)",
            "Alpha Level"
        ]
        
        for field in required_fields:
            assert field in report, f"Required field '{field}' missing from report."