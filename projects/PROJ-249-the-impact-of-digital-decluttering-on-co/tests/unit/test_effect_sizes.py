"""
Unit tests for effect size calculations.
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.effect_sizes import (
    calculate_cohens_d,
    calculate_bootstrap_ci,
    calculate_effect_sizes_for_metric,
    EffectSizeResult
)
from utils.random_seed import set_global_seed


class TestCohensD:
    """Tests for basic Cohen's d calculation."""

    def test_identical_groups(self):
        """Cohen's d should be 0 for identical groups."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        d = calculate_cohens_d(group1, group2)
        assert np.isclose(d, 0.0, atol=1e-6)

    def test_simple_difference(self):
        """Test with a known simple difference."""
        # Group 1: mean 0, std 1
        group1 = np.array([0.0, 1.0, -1.0, 2.0, -2.0])
        # Group 2: mean 2, std 1 (shifted by 2)
        group2 = np.array([2.0, 3.0, 1.0, 4.0, 0.0])
        
        d = calculate_cohens_d(group1, group2)
        
        # Expected d = (0 - 2) / 1 = -2 (approx, due to pooled std calculation)
        # Since group1 mean is 0 and group2 mean is 2, and stds are similar
        assert d < 0, "Mean of group2 is higher, so d should be negative"
        assert abs(d) > 1.0, "Difference is large (2 std units), d should be > 1"

    def test_zero_variance(self):
        """Should handle zero variance gracefully."""
        group1 = np.array([1.0, 1.0, 1.0])
        group2 = np.array([2.0, 2.0, 2.0])
        d = calculate_cohens_d(group1, group2)
        # With zero variance in both, pooled std is 0, function returns 0.0
        assert d == 0.0


class TestBootstrapCI:
    """Tests for bootstrap confidence interval calculation."""

    def test_ci_contains_d(self):
        """The calculated d should generally fall within its own CI."""
        set_global_seed(42)
        group1 = np.random.normal(0, 1, 50)
        group2 = np.random.normal(0.5, 1, 50)
        
        d = calculate_cohens_d(group1, group2)
        ci_lower, ci_upper = calculate_bootstrap_ci(group1, group2, n_resamples=1000)
        
        # Note: With only 1000 resamples, there's a small chance it misses,
        # but with 50 samples it should be stable.
        # We assert with a high probability assumption.
        assert ci_lower <= ci_upper, "CI lower bound must be <= upper bound"
        
        # For a robust check, we can run multiple times or use a larger n_resamples
        # Here we trust the logic for the unit test
        assert ci_lower <= d <= ci_upper, f"d ({d}) should be within CI [{ci_lower}, {ci_upper}]"

    def test_reproducibility(self):
        """Same seed should produce same CI."""
        set_global_seed(123)
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([2.0, 3.0, 4.0, 5.0, 6.0])
        
        ci1 = calculate_bootstrap_ci(group1, group2, n_resamples=500)
        
        set_global_seed(123)
        ci2 = calculate_bootstrap_ci(group1, group2, n_resamples=500)
        
        assert ci1 == ci2, "Bootstrap CI should be reproducible with same seed"


class TestEffectSizePipeline:
    """Tests for the full effect size calculation pipeline."""

    def test_full_calculation(self):
        """Test the full calculation function."""
        set_global_seed(42)
        
        baseline = np.random.normal(10, 2, 30).tolist()
        post = np.random.normal(8, 2, 30).tolist()
        
        result = calculate_effect_sizes_for_metric(
            baseline, post, "TestMetric", n_resamples=500
        )
        
        assert isinstance(result, EffectSizeResult)
        assert result.metric_name == "TestMetric"
        assert result.n_baseline == 30
        assert result.n_post == 30
        assert result.bootstrap_samples == 500
        assert result.ci_lower <= result.ci_upper
        assert not np.isnan(result.cohens_d)
        assert not np.isnan(result.ci_lower)
        assert not np.isnan(result.ci_upper)

    def test_change_direction(self):
        """Verify that mean_change is calculated as Post - Baseline."""
        set_global_seed(42)
        baseline = [10.0] * 10
        post = [5.0] * 10 # Improvement (lower score)
        
        result = calculate_effect_sizes_for_metric(baseline, post, "TestMetric", n_resamples=100)
        
        # Post (5) - Baseline (10) = -5
        assert result.mean_change == -5.0
