"""
Tests for validation module (F-test and BIC comparison).
"""

import pytest
import numpy as np
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.validation import (
    ModelComparisonResult,
    compute_ssr,
    compute_bic,
    perform_f_test,
    compare_null_vs_alternative,
    run_validation_analysis
)
from models.estimator import OrbitSolution
from utils.logging import AnalysisError

class TestComputeSSR:
    """Tests for sum of squared residuals computation."""

    def test_compute_ssr_basic(self):
        """Test basic SSR calculation."""
        residuals = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        expected_ssr = 1.0**2 + 2.0**2 + 3.0**2 + 4.0**2 + 5.0**2
        
        class MockSolution:
            residuals = residuals
        
        result = compute_ssr(MockSolution())
        assert np.isclose(result, expected_ssr)

    def test_compute_ssr_no_residuals(self):
        """Test that missing residuals raises error."""
        class MockSolution:
            pass
        
        with pytest.raises(AnalysisError):
            compute_ssr(MockSolution())

class TestComputeBIC:
    """Tests for BIC calculation."""

    def test_compute_bic_basic(self):
        """Test basic BIC calculation."""
        ssr = 100.0
        n_params = 5
        n_obs = 1000
        
        result = compute_bic(ssr, n_params, n_obs)
        
        # Manual calculation
        mse = ssr / n_obs
        expected = n_obs * np.log(mse) + n_params * np.log(n_obs)
        
        assert np.isclose(result, expected)

    def test_compute_bic_invalid_input(self):
        """Test that invalid inputs raise error."""
        with pytest.raises(AnalysisError):
            compute_bic(ssr=0.0, n_params=5, n_obs=1000)
        
        with pytest.raises(AnalysisError):
            compute_bic(ssr=100.0, n_params=5, n_obs=0)

class TestPerformFTest:
    """Tests for F-test implementation."""

    def test_f_test_reject_null(self):
        """Test F-test when null should be rejected."""
        ssr_null = 200.0
        df_null = 990
        ssr_alt = 100.0
        df_alt = 989
        
        f_stat, p_val, conclusion = perform_f_test(
            ssr_null, df_null, ssr_alt, df_alt, significance_level=0.05
        )
        
        assert f_stat > 0
        assert 0 <= p_val <= 1
        assert conclusion == "reject_null"

    def test_f_test_fail_to_reject(self):
        """Test F-test when null should not be rejected."""
        ssr_null = 100.5
        df_null = 990
        ssr_alt = 100.0
        df_alt = 989
        
        f_stat, p_val, conclusion = perform_f_test(
            ssr_null, df_null, ssr_alt, df_alt, significance_level=0.05
        )
        
        assert f_stat > 0
        assert 0 <= p_val <= 1
        assert conclusion == "fail_to_reject"

    def test_f_test_invalid_df(self):
        """Test F-test with invalid degrees of freedom."""
        with pytest.raises(AnalysisError):
            perform_f_test(100, 10, 50, 15)  # df_alt > df_null

class TestCompareNullVsAlternative:
    """Tests for full model comparison."""

    def test_full_comparison(self):
        """Test complete null vs alternative comparison."""
        # Create mock solutions
        class MockSolution:
            def __init__(self, ssr, n_params):
                self.residuals = np.sqrt(ssr / 100) * np.random.randn(100)
                self.n_params = n_params

        n_obs = 1000
        sol_null = MockSolution(ssr=1500, n_params=10)
        sol_alt = MockSolution(ssr=1000, n_params=11)

        result = compare_null_vs_alternative(sol_null, sol_alt, n_obs)

        assert isinstance(result, ModelComparisonResult)
        assert result.f_statistic > 0
        assert 0 <= result.p_value <= 1
        assert result.bic_null > 0
        assert result.bic_alt > 0
        assert result.df_null > 0
        assert result.df_alt > 0
        assert result.conclusion in ["reject_null", "fail_to_reject"]

class TestRunValidationAnalysis:
    """Tests for the main validation pipeline."""

    def test_run_validation_analysis(self):
        """Test full validation analysis execution."""
        class MockSolution:
            def __init__(self, ssr, n_params):
                self.residuals = np.sqrt(ssr / 100) * np.random.randn(100)
                self.n_params = n_params

        n_obs = 500
        sol_null = MockSolution(ssr=800, n_params=10)
        sol_alt = MockSolution(ssr=600, n_params=11)

        results = run_validation_analysis(sol_null, sol_alt, n_obs)

        assert "f_statistic" in results
        assert "p_value" in results
        assert "bic_null" in results
        assert "bic_alt" in results
        assert "conclusion" in results
        assert "interpretation" in results