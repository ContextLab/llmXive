"""
Tests for model diagnostics and visualization logic.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.diagnostics import calculate_vif, sensitivity_analysis, plot_coefficients

class TestVIFCalculation:
    """Unit test for VIF calculation (T025)."""

    def test_calculate_vif(self):
        """Test VIF calculation on a simple dataset."""
        # Create a dataset with known multicollinearity
        np.random.seed(42)
        n = 100
        
        # Two highly correlated variables
        x1 = np.random.normal(0, 1, n)
        x2 = x1 + np.random.normal(0, 0.1, n)  # Highly correlated with x1
        x3 = np.random.normal(0, 1, n)  # Independent
        
        data = pd.DataFrame({
            'x1': x1,
            'x2': x2,
            'x3': x3
        })

        vif_results = calculate_vif(data)

        # Verify output structure
        assert isinstance(vif_results, pd.DataFrame)
        assert 'VIF' in vif_results.columns
        assert len(vif_results) == 3

        # x1 and x2 should have high VIF due to correlation
        # x3 should have low VIF
        vif_x1 = vif_results[vif_results['variable'] == 'x1']['VIF'].values[0]
        vif_x2 = vif_results[vif_results['variable'] == 'x2']['VIF'].values[0]
        vif_x3 = vif_results[vif_results['variable'] == 'x3']['VIF'].values[0]

        assert vif_x1 > 5.0, "x1 should have high VIF due to correlation"
        assert vif_x2 > 5.0, "x2 should have high VIF due to correlation"
        assert vif_x3 < 5.0, "x3 should have low VIF"

class TestSensitivityAnalysis:
    """Integration test for sensitivity analysis sweep (T026)."""

    def test_sensitivity_analysis_sweep(self):
        """Test that sensitivity analysis runs and produces expected output."""
        # Create sample model results (odds ratios)
        sample_odds_ratios = pd.DataFrame({
            'variable': ['precipitation', 'visibility', 'temperature'],
            'odds_ratio': [1.2, 0.8, 1.05],
            'conf_int_lower': [1.1, 0.7, 0.95],
            'conf_int_upper': [1.3, 0.9, 1.15]
        })

        # Run sensitivity analysis
        result = sensitivity_analysis(sample_odds_ratios, 'precipitation')

        # Verify output structure
        assert isinstance(result, pd.DataFrame)
        assert 'threshold' in result.columns
        assert 'odds_ratio_change' in result.columns
        
        # Verify we have multiple threshold points
        assert len(result) > 1
        
        # Verify stability metric calculation
        max_change = result['odds_ratio_change'].max()
        assert max_change >= 0  # Change should be non-negative in magnitude
