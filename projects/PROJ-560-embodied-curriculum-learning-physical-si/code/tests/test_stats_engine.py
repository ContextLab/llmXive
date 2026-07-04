import pytest
import numpy as np
from typing import List, Tuple
from src.stats_engine import run_t_test, apply_bonferroni_correction, calculate_effect_size, check_collinearity, confidence_interval, calculate_power

class TestStatsEngine:
    """Tests for statistical engine functions."""

    def test_calculate_effect_size_identical_groups(self):
        """Test Cohen's d returns 0 for identical groups."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [1.0, 2.0, 3.0, 4.0, 5.0]
        d = calculate_effect_size(group1, group2)
        assert abs(d) < 1e-6, f"Expected d=0 for identical groups, got {d}"

    def test_calculate_effect_size_different_groups(self):
        """Test Cohen's d calculation with known difference."""
        # Group 1: mean=3, std~1.58
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        # Group 2: mean=6, std~1.58
        group2 = [4.0, 5.0, 6.0, 7.0, 8.0]
        
        d = calculate_effect_size(group1, group2)
        
        # Expected d approx (3-6)/1.58 = -1.9
        assert -2.5 < d < -1.5, f"Expected d around -1.9, got {d}"
        assert d < 0, "Effect size should be negative if group1 mean < group2 mean"

    def test_confidence_interval_width(self):
        """Test that CI width increases with smaller sample sizes."""
        group1_large = list(np.random.normal(0, 1, 100))
        group2_large = list(np.random.normal(0.5, 1, 100))
        group1_small = list(np.random.normal(0, 1, 10))
        group2_small = list(np.random.normal(0.5, 1, 10))
        
        lower_large, upper_large = confidence_interval(group1_large, group2_large)
        lower_small, upper_small = confidence_interval(group1_small, group2_small)
        
        width_large = upper_large - lower_large
        width_small = upper_small - lower_small
        
        assert width_small > width_large, "CI should be wider for smaller samples"

    def test_bonferroni_correction(self):
        """Test Bonferroni correction increases p-values."""
        p_values = [0.01, 0.03, 0.05, 0.10]
        adjusted, significant = apply_bonferroni_correction(p_values, alpha=0.05)
        
        assert len(adjusted) == len(p_values)
        assert all(p >= orig for p, orig in zip(adjusted, p_values)), "Adjusted p-values should be >= original"
        assert adjusted[0] == 0.01 * 4, "First adjusted p should be 0.04"
        
        # 0.04 > 0.05 -> False, 0.12 > 0.05 -> False, etc.
        assert all(s == False for s in significant), "None should be significant at 0.05 after correction"

    def test_check_collinearity_high(self):
        """Test collinearity detection with high correlation."""
        # Create perfectly correlated data
        x = list(range(100))
        y = [v * 2 + 1 for v in x]
        predictors = {"var1": x, "var2": y}
        
        result = check_collinearity(predictors, threshold=0.8)
        
        assert result["has_collinearity"] is True
        assert len(result["high_correlations"]) == 1
        assert abs(result["high_correlations"][0]["correlation"]) > 0.99

    def test_check_collinearity_low(self):
        """Test collinearity detection with low correlation."""
        np.random.seed(42)
        x = np.random.normal(0, 1, 100)
        y = np.random.normal(0, 1, 100)
        predictors = {"var1": list(x), "var2": list(y)}
        
        result = check_collinearity(predictors, threshold=0.8)
        
        assert result["has_collinearity"] is False
        assert len(result["high_correlations"]) == 0

    def test_calculate_power_sample_size(self):
        """Test that power increases with sample size."""
        effect = 0.5
        power_small = calculate_power(10, 10, effect)
        power_large = calculate_power(100, 100, effect)
        
        assert power_large > power_small, "Power should increase with sample size"

    def test_calculate_power_zero_effect(self):
        """Test power with zero effect size."""
        power = calculate_power(50, 50, 0.0)
        assert power < 0.1, "Power should be near alpha (0.05) for zero effect"

    def test_run_t_test_welch(self):
        """Test t-test with unequal variances (Welch's)."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [1.0, 1.0, 1.0, 1.0, 10.0] # High variance
        
        t_stat, p_val = run_t_test(group1, group2, equal_var=False)
        
        assert isinstance(t_stat, float)
        assert 0.0 <= p_val <= 1.0

    def test_run_t_test_student(self):
        """Test t-test with equal variances (Student's)."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [2.0, 3.0, 4.0, 5.0, 6.0]
        
        t_stat, p_val = run_t_test(group1, group2, equal_var=True)
        
        assert isinstance(t_stat, float)
        assert 0.0 <= p_val <= 1.0