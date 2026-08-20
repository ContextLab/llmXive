"""
Unit tests for analysis.py functions.
Tests partial correlation logic with mock data.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis import run_partial_correlation, run_sensitivity_analysis


class TestRunPartialCorrelation:
    """Tests for run_partial_correlation function."""

    def test_partial_correlation_with_mock_data(self):
        """Test partial correlation with known mock data."""
        # Create a mock DataFrame with known relationships
        np.random.seed(42)
        n = 100
        
        # Create variables with a known negative correlation
        cumulative_flux = np.random.uniform(1e4, 1e6, n)
        mass = np.random.uniform(0.5, 10.0, n)  # Planet mass in Earth masses
        semi_major_axis = np.random.uniform(0.05, 0.5, n)  # AU
        
        # Create retention_fraction with negative correlation to flux
        retention_fraction = 1.0 - (cumulative_flux / 1e6) * 0.8 + np.random.normal(0, 0.1, n)
        retention_fraction = np.clip(retention_fraction, 0, 1)
        
        mock_df = pd.DataFrame({
            'cumulative_flux': cumulative_flux,
            'retention_fraction': retention_fraction,
            'mass': mass,
            'semi_major_axis': semi_major_axis
        })
        
        # Run partial correlation
        rho, p_value = run_partial_correlation(mock_df)
        
        # Verify results are reasonable
        assert isinstance(rho, float), "Correlation coefficient should be a float"
        assert isinstance(p_value, float), "P-value should be a float"
        assert -1.0 <= rho <= 1.0, "Correlation coefficient must be between -1 and 1"
        assert 0.0 <= p_value <= 1.0, "P-value must be between 0 and 1"
        
        # With our mock data, we expect a negative correlation
        assert rho < 0, "Expected negative correlation in mock data"
        assert p_value < 0.05, "Expected significant correlation in mock data"

    def test_partial_correlation_with_constant_variables(self):
        """Test behavior with constant variables (should handle gracefully)."""
        mock_df = pd.DataFrame({
            'cumulative_flux': [1.0] * 10,
            'retention_fraction': [0.5] * 10,
            'mass': [2.0] * 10,
            'semi_major_axis': [0.1] * 10
        })
        
        # Should handle constant variables without crashing
        rho, p_value = run_partial_correlation(mock_df)
        
        # For constant variables, correlation is undefined or zero
        assert isinstance(rho, (float, int)), "Should return a numeric value"
        assert isinstance(p_value, (float, int)), "Should return a numeric value"

    def test_partial_correlation_with_missing_data(self):
        """Test behavior with some missing data."""
        mock_df = pd.DataFrame({
            'cumulative_flux': [1e4, 1e5, np.nan, 1e6, 5e5],
            'retention_fraction': [0.9, 0.7, 0.5, np.nan, 0.3],
            'mass': [1.0, 2.0, 3.0, 4.0, 5.0],
            'semi_major_axis': [0.1, 0.2, 0.3, 0.4, 0.5]
        })
        
        # Should handle missing data by dropping rows
        rho, p_value = run_partial_correlation(mock_df)
        
        assert isinstance(rho, float), "Should return float for correlation"
        assert isinstance(p_value, float), "Should return float for p-value"


class TestRunSensitivityAnalysis:
    """Tests for run_sensitivity_analysis function."""

    def test_sensitivity_analysis_structure(self):
        """Test that sensitivity analysis returns expected structure."""
        # Create mock data
        np.random.seed(42)
        n = 50
        
        mock_df = pd.DataFrame({
            'cumulative_flux': np.random.uniform(1e4, 1e6, n),
            'retention_fraction': np.random.uniform(0.2, 1.0, n),
            'mass': np.random.uniform(0.5, 10.0, n),
            'semi_major_axis': np.random.uniform(0.05, 0.5, n)
        })
        
        # Run sensitivity analysis
        sensitivity_results = run_sensitivity_analysis(mock_df)
        
        # Verify structure
        assert isinstance(sensitivity_results, dict), "Should return a dictionary"
        assert 'baselines' in sensitivity_results, "Should contain baselines key"
        assert 'correlations' in sensitivity_results, "Should contain correlations key"
        assert 'variation' in sensitivity_results, "Should contain variation key"
        
        # Verify types
        assert isinstance(sensitivity_results['baselines'], list), "Baselines should be a list"
        assert isinstance(sensitivity_results['correlations'], list), "Correlations should be a list"
        assert len(sensitivity_results['baselines']) == len(sensitivity_results['correlations']), \
            "Baselines and correlations should have same length"

    def test_sensitivity_analysis_variation(self):
        """Test that variation is calculated correctly."""
        np.random.seed(42)
        n = 30
        
        mock_df = pd.DataFrame({
            'cumulative_flux': np.random.uniform(1e4, 1e6, n),
            'retention_fraction': np.random.uniform(0.2, 1.0, n),
            'mass': np.random.uniform(0.5, 10.0, n),
            'semi_major_axis': np.random.uniform(0.05, 0.5, n)
        })
        
        sensitivity_results = run_sensitivity_analysis(mock_df)
        
        # Variation should be a non-negative number
        assert sensitivity_results['variation'] >= 0, "Variation should be non-negative"
        assert isinstance(sensitivity_results['variation'], (int, float)), \
            "Variation should be a numeric value"
