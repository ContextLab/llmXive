import pytest
import numpy as np
import pandas as pd
from code.analysis.stats import (
    mann_whitney_u_test,
    apply_multiple_comparison_correction,
    run_power_analysis
)
from scipy.stats import norm

class TestPowerAnalysis:
    """Tests for T025: Power analysis function implementation."""

    def test_power_analysis_basic(self):
        """Test that power analysis returns expected structure."""
        # Generate two distinct groups with a known effect
        np.random.seed(42)
        group_a = np.random.normal(loc=10, scale=2, size=100)
        group_b = np.random.normal(loc=12, scale=2, size=100)
        
        result = run_power_analysis(group_a, group_b, alpha=0.05)
        
        assert "n_group_a" in result
        assert "n_group_b" in result
        assert "effect_size_r" in result
        assert "power" in result
        assert "alpha" in result
        assert "status" in result
        
        assert result["n_group_a"] == 100
        assert result["n_group_b"] == 100
        assert result["alpha"] == 0.05
        assert result["status"] == "success"
        
        # Power should be reasonable given the effect size and sample size
        assert 0.0 <= result["power"] <= 1.0

    def test_power_analysis_small_sample(self):
        """Test power analysis with insufficient sample size."""
        group_a = np.array([1.0, 2.0])
        group_b = np.array([3.0, 4.0])
        
        result = run_power_analysis(group_a, group_b, alpha=0.05)
        
        # Should still run but might have low power or specific status
        assert "power" in result
        assert result["n_group_a"] == 2
        assert result["n_group_b"] == 2

    def test_power_analysis_insufficient_data(self):
        """Test power analysis with very small sample (< 2)."""
        group_a = np.array([1.0])
        group_b = np.array([2.0, 3.0])
        
        result = run_power_analysis(group_a, group_b, alpha=0.05)
        
        assert result["status"] == "insufficient_samples"
        assert result["power"] == 0.0

    def test_power_analysis_effect_size_calculation(self):
        """Verify that effect size is calculated and non-zero for distinct groups."""
        np.random.seed(42)
        # Create groups with a clear difference
        group_a = np.random.normal(loc=0, scale=1, size=50)
        group_b = np.random.normal(loc=1, scale=1, size=50)
        
        result = run_power_analysis(group_a, group_b)
        
        # Effect size should be positive
        assert result["effect_size_r"] > 0.0
        
    def test_power_analysis_high_power_large_sample(self):
        """Test that large samples with effect yield high power."""
        np.random.seed(42)
        group_a = np.random.normal(loc=0, scale=1, size=500)
        group_b = np.random.normal(loc=1.5, scale=1, size=500) # Larger effect
        
        result = run_power_analysis(group_a, group_b)
        
        # With large N and effect, power should be high (> 0.8 is typical target)
        assert result["power"] > 0.5 # Expecting reasonable power

class TestMannWhitneyU:
    """Regression tests for MWU to ensure power analysis inputs are valid."""

    def test_mwu_basic(self):
        group_a = np.array([1, 2, 3])
        group_b = np.array([4, 5, 6])
        stat, pval = mann_whitney_u_test(group_a, group_b)
        assert 0 <= pval <= 1

    def test_mwu_identical(self):
        group_a = np.array([1, 1, 1])
        group_b = np.array([1, 1, 1])
        stat, pval = mann_whitney_u_test(group_a, group_b)
        assert pval == 1.0

class TestMultipleComparisonCorrection:
    """Tests for T024 to ensure power analysis context is correct."""

    def test_correction_returns_lists(self):
        p_vals = [0.01, 0.02, 0.03, 0.04, 0.05]
        corrected, rejects = apply_multiple_comparison_correction(p_vals, method="fdr_bh")
        assert len(corrected) == len(p_vals)
        assert len(rejects) == len(p_vals)
        assert all(isinstance(x, float) for x in corrected)
        assert all(isinstance(x, bool) for x in rejects)
