"""Unit tests for power analysis functionality."""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from code.modeling.power_analysis import calculate_power_f_test

class TestPowerCalculation:
    """Tests for power calculation function."""

    def test_power_increases_with_sample_size(self):
        """Power should increase as sample size increases."""
        n_predictors = 10
        r_squared = 0.05
        alpha = 0.05

        power_50 = calculate_power_f_test(50, n_predictors, r_squared, alpha)
        power_100 = calculate_power_f_test(100, n_predictors, r_squared, alpha)
        power_200 = calculate_power_f_test(200, n_predictors, r_squared, alpha)

        assert power_50 < power_100 < power_200

    def test_power_increases_with_effect_size(self):
        """Power should increase as effect size (R²) increases."""
        n_samples = 100
        n_predictors = 10
        alpha = 0.05

        power_low = calculate_power_f_test(n_samples, n_predictors, 0.01, alpha)
        power_med = calculate_power_f_test(n_samples, n_predictors, 0.05, alpha)
        power_high = calculate_power_f_test(n_samples, n_predictors, 0.10, alpha)

        assert power_low < power_med < power_high

    def test_power_decreases_with_more_predictors(self):
        """Power should decrease as number of predictors increases (for fixed N)."""
        n_samples = 100
        r_squared = 0.05
        alpha = 0.05

        power_5 = calculate_power_f_test(n_samples, 5, r_squared, alpha)
        power_20 = calculate_power_f_test(n_samples, 20, r_squared, alpha)
        power_50 = calculate_power_f_test(n_samples, 50, r_squared, alpha)

        assert power_5 > power_20 > power_50

    def test_power_decreases_with_stricter_alpha(self):
        """Power should decrease as alpha becomes more stringent."""
        n_samples = 100
        n_predictors = 10
        r_squared = 0.05

        power_05 = calculate_power_f_test(n_samples, n_predictors, r_squared, 0.05)
        power_01 = calculate_power_f_test(n_samples, n_predictors, r_squared, 0.01)

        assert power_01 < power_05

    def test_sample_size_too_small_raises_error(self):
        """Should raise ValueError if sample size is too small for predictors."""
        with pytest.raises(ValueError):
            calculate_power_f_test(n_samples=5, n_predictors=10, r_squared=0.05)

    def test_typical_hypothetical_values(self):
        """Test with values typical for this project's scenario."""
        # N=100, k=20 (after PCA), R²=0.05
        power = calculate_power_f_test(100, 20, 0.05, 0.05)
        # We expect power to be in a reasonable range (0 to 1)
        assert 0.0 <= power <= 1.0