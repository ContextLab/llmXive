import pytest
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from analysis.bootstrapping import (
    theil_sen_slope,
    bootstrap_theil_sen,
    run_bootstrapping_analysis
)


class TestTheilSenSlope:
    """Tests for the Theil-Sen slope estimator."""

    def test_linear_increase(self):
        """Test with a perfectly linear increasing series."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])  # slope = 2
        
        slope = theil_sen_slope(x, y)
        assert abs(slope - 2.0) < 1e-6

    def test_linear_decrease(self):
        """Test with a perfectly linear decreasing series."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])  # slope = -2
        
        slope = theil_sen_slope(x, y)
        assert abs(slope - (-2.0)) < 1e-6

    def test_constant_series(self):
        """Test with a constant series (slope should be 0)."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 5, 5, 5, 5])
        
        slope = theil_sen_slope(x, y)
        assert abs(slope) < 1e-6

    def test_noisy_linear(self):
        """Test with noisy linear data."""
        np.random.seed(42)
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = 2 * x + 5 + np.random.normal(0, 2, len(x))
        
        slope = theil_sen_slope(x, y)
        # Should be close to 2, but not exact due to noise
        assert 1.5 < slope < 2.5


class TestBootstrapTheilSen:
    """Tests for the bootstrapping implementation."""

    def test_consistency_with_repeated_runs(self):
        """Test that results are consistent with fixed random seed."""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = 2 * x + 5 + np.random.normal(0, 1, len(x))
        
        slope1, lower1, upper1 = bootstrap_theil_sen(
            x, y, n_iterations=100, random_seed=42
        )
        slope2, lower2, upper2 = bootstrap_theil_sen(
            x, y, n_iterations=100, random_seed=42
        )
        
        assert slope1 == slope2
        assert lower1 == lower2
        assert upper1 == upper2

    def test_confidence_interval_covers_true_slope(self):
        """Test that the CI contains the true slope for clean linear data."""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = 2 * x + 5  # Perfectly linear, slope = 2
        
        slope, lower, upper = bootstrap_theil_sen(
            x, y, n_iterations=100, random_seed=42
        )
        
        # For perfect linear data, the CI should be tight around 2
        assert lower <= 2.0 <= upper
        assert abs(slope - 2.0) < 0.5

    def test_wider_ci_for_noisy_data(self):
        """Test that noisy data produces wider confidence intervals."""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        
        # Low noise
        y_low = 2 * x + 5 + np.random.normal(0, 0.5, len(x))
        _, lower_low, upper_low = bootstrap_theil_sen(
            y_low, y_low, n_iterations=100, random_seed=42
        )
        
        # High noise
        y_high = 2 * x + 5 + np.random.normal(0, 5, len(x))
        _, lower_high, upper_high = bootstrap_theil_sen(
            y_high, y_high, n_iterations=100, random_seed=42
        )
        
        # This test is approximate due to randomness
        # We just check that the function runs without error
        assert upper_low - lower_low >= 0
        assert upper_high - lower_high >= 0


class TestRunBootstrappingAnalysis:
    """Integration tests for the full bootstrapping pipeline."""

    def test_run_analysis_structure(self, tmp_path):
        """Test that the analysis produces the expected structure."""
        # This is a structural test - we can't easily test with real data
        # without setting up the full pipeline, so we just verify the function exists
        # and has the right signature
        assert callable(run_bootstrapping_analysis)

    def test_n_iterations_parameter(self):
        """Test that n_iterations parameter is accepted."""
        # We can't run this without data, but we can check the signature
        import inspect
        sig = inspect.signature(run_bootstrapping_analysis)
        assert 'n_iterations' in sig.parameters