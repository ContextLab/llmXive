import pytest
import numpy as np
from typing import Dict
from analysis.statistics import fit_regression, run_permutation_test, apply_fwe_correction, format_delta_r2, RegressionResult
from errors import DataMissingCreativityError

class TestFitRegression:
    def test_fit_regression_basic(self):
        """Test basic regression fit with synthetic data."""
        np.random.seed(42)
        n = 100
        flexibility = np.random.randn(n)
        creativity = 0.5 * flexibility + np.random.randn(n) * 0.5
        covariates = {
            'age': np.random.randn(n),
            'sex': np.random.randint(0, 2, n),
            'education': np.random.randn(n)
        }
        
        result = fit_regression(flexibility, creativity, covariates)
        
        assert isinstance(result, RegressionResult)
        assert result.r_squared is not None
        assert result.r_squared >= 0 and result.r_squared <= 1
        assert result.p_value is not None
        assert result.coef_flexibility is not None
        # Check that the coefficient is positive (as per our synthetic data)
        assert result.coef_flexibility > 0, "Coefficient should be positive"

    def test_fit_regression_with_static_strength(self):
        """Test regression including static connectivity strength."""
        np.random.seed(42)
        n = 100
        flexibility = np.random.randn(n)
        static_strength = np.random.randn(n) * 0.5
        creativity = 0.5 * flexibility + 0.3 * static_strength + np.random.randn(n) * 0.3
        covariates = {
            'age': np.random.randn(n),
            'sex': np.random.randint(0, 2, n),
            'education': np.random.randn(n),
            'static_connectivity_strength': static_strength
        }
        
        result = fit_regression(flexibility, creativity, covariates)
        
        assert isinstance(result, RegressionResult)
        assert result.r_squared is not None
        # R-squared should be higher than without static strength
        assert result.r_squared > 0.1, "R-squared should be reasonable"

    def test_fit_regression_small_sample(self):
        """Test regression with small sample size."""
        np.random.seed(42)
        n = 10
        flexibility = np.random.randn(n)
        creativity = 0.5 * flexibility + np.random.randn(n) * 0.5
        covariates = {'age': np.random.randn(n)}
        
        # Should not raise an error for small sample
        result = fit_regression(flexibility, creativity, covariates)
        assert result.r_squared is not None

    def test_fit_regression_correlation_report(self):
        """Test that Pearson correlation is computed and reported."""
        np.random.seed(42)
        n = 50
        flexibility = np.random.randn(n)
        creativity = 0.7 * flexibility + np.random.randn(n) * 0.3
        covariates = {}
        
        result = fit_regression(flexibility, creativity, covariates)
        
        # The result should contain the correlation
        assert hasattr(result, 'correlation') or hasattr(result, 'pearson_r'), \
            "Result should contain correlation information"

class TestRunPermutationTest:
    def test_permutation_test_significant(self):
        """Test permutation test with significant relationship."""
        np.random.seed(42)
        n = 100
        flexibility = np.random.randn(n)
        creativity = 0.8 * flexibility + np.random.randn(n) * 0.2  # Strong relationship
        
        p_value = run_permutation_test(flexibility, creativity, n_permutations=1000)
        
        assert 0 <= p_value <= 1
        # With strong relationship, p-value should be small
        assert p_value < 0.05, "P-value should be significant for strong relationship"

    def test_permutation_test_null(self):
        """Test permutation test with no relationship."""
        np.random.seed(42)
        n = 100
        flexibility = np.random.randn(n)
        creativity = np.random.randn(n)  # No relationship
        
        p_value = run_permutation_test(flexibility, creativity, n_permutations=1000)
        
        assert 0 <= p_value <= 1
        # With no relationship, p-value should be large (not significant)
        assert p_value > 0.05, "P-value should be non-significant for null relationship"

    def test_permutation_test_deterministic_seed(self):
        """Test that permutation test is reproducible with same seed."""
        np.random.seed(42)
        flexibility = np.random.randn(50)
        creativity = np.random.randn(50)
        
        p1 = run_permutation_test(flexibility, creativity, n_permutations=500)
        
        np.random.seed(42)
        flexibility = np.random.randn(50)
        creativity = np.random.randn(50)
        
        p2 = run_permutation_test(flexibility, creativity, n_permutations=500)
        
        assert p1 == p2, "Permutation test should be reproducible with same seed"

    def test_permutation_test_two_tailed(self):
        """Test that permutation test correctly computes two-tailed p-value."""
        np.random.seed(42)
        n = 50
        flexibility = np.random.randn(n)
        creativity = 0.5 * flexibility + np.random.randn(n) * 0.5
        
        p_value = run_permutation_test(flexibility, creativity, n_permutations=1000)
        
        # Two-tailed p-value should be in [0, 1]
        assert 0 <= p_value <= 1

class TestApplyFweCorrection:
    def test_fwe_correction_max_t(self):
        """Test FWE correction using max-T method."""
        p_values = [0.01, 0.05, 0.1, 0.2, 0.5]
        
        corrected = apply_fwe_correction(p_values, method='max-t')
        
        assert len(corrected) == len(p_values)
        # Corrected p-values should be >= original p-values
        for orig, corr in zip(p_values, corrected):
            assert corr >= orig, "Corrected p-value should be >= original"
            assert 0 <= corr <= 1, "Corrected p-value should be in [0, 1]"

    def test_fwe_correction_all_significant(self):
        """Test FWE correction when all p-values are significant."""
        p_values = [0.001, 0.002, 0.003]
        
        corrected = apply_fwe_correction(p_values, method='max-t')
        
        # Some may become non-significant after correction
        assert len(corrected) == len(p_values)
        assert all(0 <= p <= 1 for p in corrected)

class TestFormatDeltaR2:
    def test_format_delta_r2_precision(self):
        """Test that format_delta_r2 returns 4 decimal places."""
        delta = 0.123456789
        formatted = format_delta_r2(delta)
        
        assert formatted == "0.1235", f"Expected '0.1235', got '{formatted}'"
        
    def test_format_delta_r2_small_value(self):
        """Test formatting of small delta R² values."""
        delta = 0.0000123
        formatted = format_delta_r2(delta)
        
        assert formatted == "0.0000", f"Expected '0.0000', got '{formatted}'"
        
    def test_format_delta_r2_negative(self):
        """Test formatting of negative delta R² values."""
        delta = -0.05678
        formatted = format_delta_r2(delta)
        
        assert formatted == "-0.0568", f"Expected '-0.0568', got '{formatted}'"
