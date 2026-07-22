"""
Unit tests for statistical analysis module.

Tests for paired t-tests, Cohen's d, confidence intervals, and Bonferroni correction.
"""

import pytest
import numpy as np
from scipy import stats
from code.analysis.stats import (
    calculate_cohen_d,
    calculate_confidence_interval,
    bonferroni_correction,
    run_paired_ttest,
    calculate_percentage_difference,
    StatisticalTestResult
)

class TestCohenD:
    """Tests for Cohen's d effect size calculation."""
    
    def test_cohen_d_basic(self):
        """Test basic Cohen's d calculation with known values."""
        group1 = np.array([10, 12, 14, 16, 18])
        group2 = np.array([8, 10, 12, 14, 16])
        
        d = calculate_cohen_d(group1, group2)
        
        # Manual calculation:
        # mean1 = 14, mean2 = 12
        # std1 = sqrt(10) ≈ 3.16, std2 = sqrt(10) ≈ 3.16
        # pooled_std = sqrt(10) ≈ 3.16
        # d = (14 - 12) / 3.16 ≈ 0.63
        assert 0.6 < d < 0.7, f"Expected d ≈ 0.63, got {d}"
    
    def test_cohen_d_zero_effect(self):
        """Test Cohen's d when groups are identical."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([1, 2, 3, 4, 5])
        
        d = calculate_cohen_d(group1, group2)
        assert d == 0.0, f"Expected d = 0, got {d}"
    
    def test_cohen_d_large_effect(self):
        """Test Cohen's d with large effect size."""
        group1 = np.array([20, 22, 24, 26, 28])
        group2 = np.array([8, 10, 12, 14, 16])
        
        d = calculate_cohen_d(group1, group2)
        assert d > 2.0, f"Expected large effect (d > 2), got {d}"
    
    def test_cohen_d_insufficient_samples(self):
        """Test that Cohen's d raises error with insufficient samples."""
        group1 = np.array([1, 2])
        group2 = np.array([1])
        
        with pytest.raises(ValueError, match="at least 2 samples"):
            calculate_cohen_d(group1, group2)

class TestConfidenceInterval:
    """Tests for confidence interval calculation."""
    
    def test_confidence_interval_narrow(self):
        """Test CI with low variance (should be narrow)."""
        group1 = np.array([10.0, 10.1, 9.9, 10.0, 10.0])
        group2 = np.array([8.0, 8.1, 7.9, 8.0, 8.0])
        
        ci = calculate_confidence_interval(group1, group2)
        
        # Difference should be around 2.0
        diff = np.mean(group1) - np.mean(group2)
        assert abs(diff - 2.0) < 0.1
        # CI should contain the difference
        assert ci[0] <= diff <= ci[1]
        # CI should be relatively narrow
        width = ci[1] - ci[0]
        assert width < 1.0, f"Expected narrow CI, got width {width}"
    
    def test_confidence_interval_wide(self):
        """Test CI with high variance (should be wide)."""
        group1 = np.array([1, 10, 2, 9, 3])
        group2 = np.array([5, 15, 6, 14, 7])
        
        ci = calculate_confidence_interval(group1, group2)
        
        # CI should be wider than in low variance case
        width = ci[1] - ci[0]
        assert width > 5.0, f"Expected wide CI, got width {width}"
    
    def test_confidence_interval_includes_zero(self):
        """Test CI when groups are similar (should include zero)."""
        group1 = np.array([10, 11, 12, 13, 14])
        group2 = np.array([10.5, 11.5, 12.5, 13.5, 14.5])
        
        ci = calculate_confidence_interval(group1, group2)
        
        # Difference is -0.5, CI should include zero
        assert ci[0] < 0 < ci[1], f"CI {ci} should include zero"

class TestBonferroniCorrection:
    """Tests for Bonferroni correction."""
    
    def test_bonferroni_basic(self):
        """Test basic Bonferroni correction."""
        p_values = [0.01, 0.05, 0.10, 0.20]
        adjusted = bonferroni_correction(p_values)
        
        # Each p-value should be multiplied by n_tests (4)
        expected = [0.04, 0.20, 0.40, 0.80]
        
        for a, e in zip(adjusted, expected):
            assert abs(a - e) < 0.001, f"Expected {e}, got {a}"
    
    def test_bonferroni_capped_at_one(self):
        """Test that Bonferroni correction caps at 1.0."""
        p_values = [0.3, 0.4, 0.5, 0.6]
        adjusted = bonferroni_correction(p_values)
        
        # 0.6 * 4 = 2.4, should be capped at 1.0
        assert adjusted[3] == 1.0, f"Expected 1.0, got {adjusted[3]}"
        
        # All values should be <= 1.0
        for a in adjusted:
            assert a <= 1.0, f"Adjusted p-value {a} exceeds 1.0"
    
    def test_bonferroni_empty_list(self):
        """Test Bonferroni with empty list."""
        adjusted = bonferroni_correction([])
        assert adjusted == [], "Empty list should return empty list"
    
    def test_bonferroni_single_value(self):
        """Test Bonferroni with single p-value."""
        p_values = [0.05]
        adjusted = bonferroni_correction(p_values)
        
        # Single test: no correction needed
        assert abs(adjusted[0] - 0.05) < 0.001

class TestPairedTtest:
    """Tests for paired t-test wrapper."""
    
    def test_paired_ttest_basic(self):
        """Test basic paired t-test."""
        # Create correlated data (same seed effect)
        np.random.seed(42)
        base = np.random.normal(0.7, 0.05, 10)
        recursive = base + np.random.normal(0.05, 0.02, 10)  # Slightly higher
        baseline = base + np.random.normal(0.0, 0.02, 10)
        
        result = run_paired_ttest(recursive, baseline, "test_metric")
        
        assert isinstance(result, StatisticalTestResult)
        assert result.metric_name == "test_metric"
        assert result.group1_mean > result.group2_mean  # recursive > baseline
        assert result.n_samples == 10
        assert result.t_statistic != 0  # Should show some difference
    
    def test_paired_ttest_significant(self):
        """Test paired t-test with clearly significant difference."""
        recursive = np.array([0.85, 0.87, 0.84, 0.86, 0.88])
        baseline = np.array([0.65, 0.67, 0.64, 0.66, 0.68])
        
        result = run_paired_ttest(recursive, baseline, "significant_test")
        
        # Should be significant
        assert result.p_value < 0.05, f"Expected p < 0.05, got {result.p_value}"
        assert abs(result.t_statistic) > 4.0, f"Expected large t-stat, got {result.t_statistic}"
    
    def test_paired_ttest_mismatched_sizes(self):
        """Test that mismatched sizes raise error."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([1, 2, 3, 4])
        
        with pytest.raises(ValueError, match="same size"):
            run_paired_ttest(group1, group2, "test")
    
    def test_paired_ttest_insufficient_samples(self):
        """Test that insufficient samples raise error."""
        group1 = np.array([1, 2])
        group2 = np.array([1, 2])
        
        # This should work (n=2 is minimum)
        result = run_paired_ttest(group1, group2, "test")
        assert result.n_samples == 2
        
        # n=1 should fail
        group1 = np.array([1])
        group2 = np.array([1])
        
        with pytest.raises(ValueError, match="at least 2 samples"):
            run_paired_ttest(group1, group2, "test")

class TestPercentageDifference:
    """Tests for percentage difference calculation."""
    
    def test_percentage_difference_positive(self):
        """Test positive percentage difference."""
        group1 = np.array([120])
        group2 = np.array([100])
        
        diff = calculate_percentage_difference(group1, group2)
        assert diff == 20.0, f"Expected 20%, got {diff}"
    
    def test_percentage_difference_negative(self):
        """Test negative percentage difference."""
        group1 = np.array([80])
        group2 = np.array([100])
        
        diff = calculate_percentage_difference(group1, group2)
        assert diff == -20.0, f"Expected -20%, got {diff}"
    
    def test_percentage_difference_zero(self):
        """Test zero percentage difference."""
        group1 = np.array([100])
        group2 = np.array([100])
        
        diff = calculate_percentage_difference(group1, group2)
        assert diff == 0.0, f"Expected 0%, got {diff}"
    
    def test_percentage_difference_zero_baseline(self):
        """Test handling of zero baseline (should return 0)."""
        group1 = np.array([100])
        group2 = np.array([0])
        
        diff = calculate_percentage_difference(group1, group2)
        assert diff == 0.0, f"Expected 0% for zero baseline, got {diff}"

class TestStatisticalTestResult:
    """Tests for StatisticalTestResult dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = StatisticalTestResult(
            test_name="paired_ttest",
            metric_name="self_consistency",
            group1_mean=0.75,
            group2_mean=0.65,
            t_statistic=3.5,
            p_value=0.002,
            effect_size_cohen_d=1.2,
            confidence_interval_95=(0.05, 0.15),
            is_significant_after_bonferroni=True,
            bonferroni_adjusted_p_value=0.008,
            n_samples=10
        )
        
        d = result.to_dict()
        
        assert d["test_name"] == "paired_ttest"
        assert d["metric_name"] == "self_consistency"
        assert d["group1_mean"] == 0.75
        assert d["t_statistic"] == 3.5
        assert d["is_significant_after_bonferroni"] is True
        assert d["confidence_interval_95"] == [0.05, 0.15]
        assert d["n_samples"] == 10
        assert "effect_size_cohen_d" in d
        assert "p_value" in d
        assert "bonferroni_adjusted_p_value" in d