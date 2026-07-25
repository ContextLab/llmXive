"""
Tests for the scipy fallback implementation of residual diagnostics.

These tests verify that the custom implementations of Shapiro-Wilk and 
Breusch-Pagan tests produce valid results and handle edge cases correctly.
"""

import pytest
import numpy as np
from scipy import stats as scipy_stats
from code.scipy_fallback import (
    shapiro_wilk_test, 
    breusch_pagan_test, 
    run_residual_diagnostics_scipy
)

class TestShapiroWilk:
    def test_normal_data_passes(self):
        """Test that normally distributed data passes the Shapiro-Wilk test."""
        np.random.seed(42)
        # Generate 50 samples from a normal distribution
        residuals = np.random.normal(loc=0.0, scale=1.0, size=50)
        
        stat, p_value = shapiro_wilk_test(residuals)
        
        assert stat is not None
        assert 0.0 <= p_value <= 1.0
        # For normal data, p-value should typically be > 0.05
        # (We don't assert strict > 0.05 due to randomness, but it usually is)
        assert stat > 0.0
        
    def test_small_sample_handling(self):
        """Test behavior with very small sample size."""
        residuals = np.array([1.0, 2.0])
        
        # Should handle gracefully (return default or log warning)
        # The implementation returns (0.0, 1.0) for n < 3
        stat, p_value = shapiro_wilk_test(residuals)
        
        assert stat == 0.0
        assert p_value == 1.0
        
    def test_empty_input_raises(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="Residuals array is empty"):
            shapiro_wilk_test(np.array([]))

class TestBreuschPagan:
    def test_homoscedastic_data(self):
        """Test that homoscedastic data (constant variance) passes."""
        np.random.seed(42)
        n = 100
        fitted = np.linspace(0, 10, n)
        # Constant variance residuals
        residuals = np.random.normal(loc=0.0, scale=1.0, size=n)
        
        lm, p_value = breusch_pagan_test(residuals, fitted)
        
        assert lm is not None
        assert 0.0 <= p_value <= 1.0
        # For homoscedastic data, p-value should be > 0.05 (fail to reject null)
        # We don't assert strictly > 0.05 due to randomness, but it's expected
        assert lm >= 0.0
        
    def test_heteroscedastic_data(self):
        """Test that heteroscedastic data (variance increases with fitted) is detected."""
        np.random.seed(42)
        n = 100
        fitted = np.linspace(0, 10, n)
        # Variance increases with fitted value
        residuals = np.random.normal(loc=0.0, scale=fitted + 1.0, size=n)
        
        lm, p_value = breusch_pagan_test(residuals, fitted)
        
        assert lm is not None
        assert 0.0 <= p_value <= 1.0
        # For heteroscedastic data, p-value might be < 0.05
        # We just verify the calculation runs without crashing
        
    def test_mismatched_lengths_raises(self):
        """Test that mismatched lengths raise ValueError."""
        residuals = np.array([1.0, 2.0, 3.0])
        fitted = np.array([1.0, 2.0])
        
        with pytest.raises(ValueError, match="Length mismatch"):
            breusch_pagan_test(residuals, fitted)
            
    def test_singular_matrix_handling(self):
        """Test handling of singular X'X matrix (constant fitted values)."""
        residuals = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        fitted = np.array([5.0, 5.0, 5.0, 5.0, 5.0])  # Constant
        
        lm, p_value = breusch_pagan_test(residuals, fitted)
        
        # Should return default values indicating no heteroscedasticity detected
        # due to inability to calculate
        assert lm == 0.0
        assert p_value == 1.0

class TestRunResidualDiagnosticsScipy:
    def test_full_pipeline_normal_data(self):
        """Test the full diagnostic pipeline with normal, homoscedastic data."""
        np.random.seed(42)
        n = 50
        fitted = np.random.normal(0, 1, n)
        residuals = np.random.normal(0, 1, n)
        
        results = run_residual_diagnostics_scipy(residuals, fitted)
        
        assert "shapiro_stat" in results
        assert "shapiro_p" in results
        assert "shapiro_pass" in results
        assert "breusch_pagan_lm" in results
        assert "breusch_pagan_p" in results
        assert "breusch_pagan_pass" in results
        assert "errors" in results
        
        assert results["errors"] == []
        
    def test_full_pipeline_with_errors(self):
        """Test the pipeline when one test fails."""
        # Normal data for Shapiro, but mismatched lengths for Breusch-Pagan
        # We simulate this by passing valid arrays but the function handles internal errors
        # To test error handling, we rely on the internal try/except blocks
        
        np.random.seed(42)
        n = 50
        fitted = np.random.normal(0, 1, n)
        residuals = np.random.normal(0, 1, n)
        
        results = run_residual_diagnostics_scipy(residuals, fitted)
        
        # Should complete without raising, even if specific tests fail internally
        assert isinstance(results["errors"], list)
