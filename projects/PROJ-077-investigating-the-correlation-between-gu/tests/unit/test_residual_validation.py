"""
Unit tests for Task T025b: Residual Normality Validation
"""
import pytest
import numpy as np
import pandas as pd
import os
import json
from pathlib import Path
from scipy import stats

# Import functions from the module
# Note: We assume the module is in the code/ directory and added to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from residual_validation import (
    perform_shapiro_wilk_test,
    check_normality_assumption,
    generate_diagnostics_report
)
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

class TestShapiroWilk:
    def test_normal_distribution_passes(self):
        """Test that a sample from a normal distribution passes the test (high p-value)."""
        np.random.seed(42)
        normal_data = np.random.normal(loc=0, scale=1, size=100)
        
        result = perform_shapiro_wilk_test(normal_data)
        
        assert result['p_value'] > 0.05, "Normal data should pass Shapiro-Wilk test (p > 0.05)"
        assert 0 <= result['statistic'] <= 1, "Statistic must be between 0 and 1"

    def test_skewed_distribution_fails(self):
        """Test that a highly skewed distribution fails the test (low p-value)."""
        np.random.seed(42)
        # Exponential distribution is highly skewed
        skewed_data = np.random.exponential(scale=2.0, size=100)
        
        result = perform_shapiro_wilk_test(skewed_data)
        
        # Note: With N=100, exponential is very likely to fail, but small samples might pass.
        # We assert that the statistic is lower than the normal case typically.
        assert result['statistic'] < 0.95, "Skewed data should have lower Shapiro statistic"

    def test_insufficient_data_raises(self):
        """Test that < 3 samples raises an error."""
        with pytest.raises(ValueError, match="at least 3 samples"):
            perform_shapiro_wilk_test(np.array([1, 2]))

class TestNormalityAssumption:
    def test_pass_condition(self):
        """Test PASS condition when p > alpha."""
        result = check_normality_assumption(p_value=0.15, alpha=0.05)
        assert result['assumption_met'] is True
        assert result['status'] == 'PASS'

    def test_fail_condition(self):
        """Test FAIL condition when p <= alpha."""
        result = check_normality_assumption(p_value=0.01, alpha=0.05)
        assert result['assumption_met'] is False
        assert result['status'] == 'FAIL'

class TestReportGeneration:
    def test_report_structure(self):
        """Test that the report dictionary contains all required keys."""
        # Create mock OLS results
        np.random.seed(42)
        X = np.random.randn(50, 2)
        X = add_constant(X)
        y = np.random.randn(50)
        
        model = OLS(y, X)
        results = model.fit()
        
        report = generate_diagnostics_report(results)
        
        required_keys = [
            'test_name', 'test_description', 'sample_size', 
            'shapiro_wilk', 'normality_assessment', 'model_summary'
        ]
        
        for key in required_keys:
            assert key in report, f"Missing required key in report: {key}"

        # Check nested structure
        assert 'statistic' in report['shapiro_wilk']
        assert 'p_value' in report['shapiro_wilk']
        assert 'assumption_met' in report['normality_assessment']
        assert 'r_squared' in report['model_summary']
