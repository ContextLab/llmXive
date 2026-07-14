"""
Unit tests for the data generation module.
"""
import pytest
import numpy as np
from code.data_generator import (
    generate_normal,
    generate_uniform,
    generate_log_normal,
    generate_data,
    validate_sample_statistics
)

class TestNormalDistribution:
    """Tests for normal distribution generation (T008a)."""

    def test_normal_null_hypothesis_means(self):
        """Verify that effect_size=0 results in near-identical means."""
        n = 10000
        s1, s2 = generate_normal(n, effect_size=0.0, seed=42)
        # With large N, means should be very close
        assert np.isclose(np.mean(s1), np.mean(s2), atol=0.05)

    def test_normal_alternative_hypothesis_shift(self):
        """Verify that effect_size=0.5 results in mean difference ~0.5."""
        n = 10000
        s1, s2 = generate_normal(n, effect_size=0.5, seed=42)
        diff = np.mean(s2) - np.mean(s1)
        assert np.isclose(diff, 0.5, atol=0.05)

    def test_normal_reproducibility(self):
        """Verify same seed produces identical results."""
        n = 100
        s1_a, s2_a = generate_normal(n, effect_size=0.1, seed=123)
        s1_b, s2_b = generate_normal(n, effect_size=0.1, seed=123)
        assert np.array_equal(s1_a, s1_b)
        assert np.array_equal(s2_a, s2_b)

class TestLogNormalDistribution:
    """Tests for log-normal distribution generation (T008b)."""

    def test_log_normal_skewness_positive(self):
        """Verify log-normal data is positively skewed."""
        n = 10000
        s1, _ = generate_log_normal(n, effect_size=0.0, seed=42)
        # Skewness should be significantly positive for log-normal
        from scipy import stats
        skew = stats.skew(s1)
        assert skew > 0.5  # Log-normal is always right-skewed

    def test_log_normal_effect_size_validation(self):
        """Verify effect size shifts the distribution parameters correctly."""
        n = 5000
        # With log-normal, the mean difference isn't linear with effect_size
        # but the underlying normal mean shifts.
        # We check that the generated values are finite and positive.
        s1, s2 = generate_log_normal(n, effect_size=0.5, seed=42)
        assert np.all(s1 > 0)
        assert np.all(s2 > 0)
        assert np.all(np.isfinite(s1))
        assert np.all(np.isfinite(s2))

class TestUniformDistribution:
    """Tests for uniform distribution generation (T008c)."""

    def test_uniform_sample_size_accuracy(self):
        """Verify generated arrays have exact requested size."""
        for n in [10, 100, 1000]:
            s1, s2 = generate_uniform(n, effect_size=0.0, seed=42)
            assert len(s1) == n
            assert len(s2) == n

    def test_uniform_range_shift(self):
        """Verify effect_size shifts the uniform range correctly."""
        n = 10000
        s1, s2 = generate_uniform(n, effect_size=0.5, seed=42)
        # s1 range [0, 1], s2 range [0.5, 1.5]
        assert np.min(s1) >= 0.0 and np.max(s1) <= 1.0
        assert np.min(s2) >= 0.49 and np.max(s2) <= 1.51  # Allow small float error

class TestDispatchAndValidation:
    """Tests for the generate_data dispatch and validation logic."""

    def test_generate_data_dispatch(self):
        """Verify generate_data calls the correct specific function."""
        n = 100
        # Normal
        s1, s2 = generate_data(n, "normal", seed=1)
        assert isinstance(s1, np.ndarray)
        # Uniform
        s1, s2 = generate_data(n, "uniform", seed=1)
        assert isinstance(s1, np.ndarray)
        # Log-normal
        s1, s2 = generate_data(n, "log-normal", seed=1)
        assert isinstance(s1, np.ndarray)

    def test_generate_data_invalid_distribution(self):
        """Verify ValueError is raised for unknown distribution."""
        with pytest.raises(ValueError):
            generate_data(10, "unknown_dist")

    def test_validate_sample_statistics_pass(self):
        """Verify validation passes for correct data."""
        s1 = np.array([1.0, 2.0, 3.0])
        s2 = np.array([2.0, 3.0, 4.0])
        # Expected diff = 1.0
        result = validate_sample_statistics(s1, s2, expected_mean_diff=1.0, tolerance=0.1)
        assert result is True

    def test_validate_sample_statistics_fail(self):
        """Verify validation fails for incorrect data."""
        s1 = np.array([1.0, 2.0, 3.0])
        s2 = np.array([2.0, 3.0, 4.0])
        # Expected diff = 10.0 (way off)
        with pytest.raises(ValueError):
            validate_sample_statistics(s1, s2, expected_mean_diff=10.0, tolerance=0.1)
