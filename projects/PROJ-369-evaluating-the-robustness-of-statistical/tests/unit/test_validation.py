"""
Unit tests for synthetic data validation (User Story 2).

These tests verify that the validation module correctly identifies
valid and invalid synthetic data generation.
"""

import pytest
import numpy as np
from src.synthesis.validation import (
    compute_acf_lag1,
    shuffle_series,
    validate_shuffled_acf,
    validate_baseline_hurst,
    validate_synthetic_generation,
    validate_all_synthetic_series
)
from src.utils.config import set_seed


@pytest.fixture
def white_noise_series():
    """Generate a white noise series for testing."""
    set_seed(42)
    rng = np.random.default_rng(42)
    return rng.standard_normal(1000)


@pytest.fixture
def correlated_series():
    """Generate a correlated series for testing."""
    set_seed(123)
    rng = np.random.default_rng(123)
    n = 1000
    # Create an AR(1) process with phi=0.7
    ar1 = np.zeros(n)
    ar1[0] = rng.standard_normal()
    for i in range(1, n):
        ar1[i] = 0.7 * ar1[i-1] + rng.standard_normal()
    return ar1


class TestACFLag1:
    """Tests for ACF lag-1 computation."""

    def test_white_noise_acf_near_zero(self, white_noise_series):
        """White noise should have ACF lag-1 close to 0."""
        acf_lag1 = compute_acf_lag1(white_noise_series)
        # For white noise, ACF lag-1 should be small (not exactly 0 due to sampling)
        assert abs(acf_lag1) < 0.1, f"ACF lag-1 for white noise should be near 0, got {acf_lag1}"

    def test_correlated_series_positive_acf(self, correlated_series):
        """Correlated series should have positive ACF lag-1."""
        acf_lag1 = compute_acf_lag1(correlated_series)
        assert acf_lag1 > 0.3, f"Correlated series should have positive ACF lag-1, got {acf_lag1}"

    def test_single_element(self):
        """Single element series should return 0."""
        series = np.array([1.0])
        acf_lag1 = compute_acf_lag1(series)
        assert acf_lag1 == 0.0

    def test_empty_series(self):
        """Empty series should return 0."""
        series = np.array([])
        acf_lag1 = compute_acf_lag1(series)
        assert acf_lag1 == 0.0


class TestShuffleSeries:
    """Tests for series shuffling."""

    def test_shuffle_preserves_values(self, white_noise_series):
        """Shuffled series should contain the same values."""
        set_seed(42)
        rng = np.random.default_rng(42)
        shuffled = shuffle_series(white_noise_series, rng)

        # Check that sorted values are identical
        assert np.allclose(np.sort(white_noise_series), np.sort(shuffled))

    def test_shuffle_changes_order(self, white_noise_series):
        """Shuffled series should generally have different order."""
        set_seed(42)
        rng = np.random.default_rng(42)
        shuffled = shuffle_series(white_noise_series, rng)

        # With high probability, the order should change
        # (unless all values are identical, which is unlikely for normal distribution)
        assert not np.array_equal(white_noise_series, shuffled) or \
               len(np.unique(white_noise_series)) == 1

    def test_reproducible_shuffle(self, white_noise_series):
        """Shuffling with same seed should produce same result."""
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)

        shuffled1 = shuffle_series(white_noise_series.copy(), rng1)
        shuffled2 = shuffle_series(white_noise_series.copy(), rng2)

        assert np.array_equal(shuffled1, shuffled2)


class TestShuffledACFValidation:
    """Tests for shuffled ACF validation."""

    def test_white_noise_passes_validation(self, white_noise_series):
        """White noise should pass shuffled ACF validation."""
        result = validate_shuffled_acf(white_noise_series, n_trials=100, seed=42)

        assert result['passed'], f"White noise should pass validation: {result}"
        assert result['within_tolerance'], f"Mean ACF should be within tolerance: {result}"
        assert abs(result['mean_acf_lag1']) < 0.05

    def test_validation_returns_expected_keys(self, white_noise_series):
        """Validation result should contain all expected keys."""
        result = validate_shuffled_acf(white_noise_series, n_trials=10, seed=42)

        expected_keys = [
            'mean_acf_lag1', 'std_acf_lag1', 'min_acf_lag1', 'max_acf_lag1',
            'within_tolerance', 'passed', 'n_trials', 'series_length', 'seed'
        ]

        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_multiple_trials(self, white_noise_series):
        """Validation should perform the specified number of trials."""
        n_trials = 50
        result = validate_shuffled_acf(white_noise_series, n_trials=n_trials, seed=42)

        assert result['n_trials'] == n_trials


class TestBaselineHurstValidation:
    """Tests for baseline Hurst validation."""

    def test_white_noise_hurst_near_05(self, white_noise_series):
        """White noise should have Hurst exponent near 0.5."""
        # Note: This test may be flaky due to DFA estimation variance
        # We use a relatively loose tolerance
        result = validate_baseline_hurst(white_noise_series, expected_h=0.5, tolerance=0.15, seed=42)

        # The validation should at least compute a reasonable value
        assert 0.3 <= result['estimated_h'] <= 0.7, \
            f"Hurst estimate should be reasonable: {result['estimated_h']}"

    def test_validation_returns_expected_keys(self, white_noise_series):
        """Validation result should contain all expected keys."""
        result = validate_baseline_hurst(white_noise_series, seed=42)

        expected_keys = [
            'estimated_h', 'expected_h', 'deviation',
            'within_tolerance', 'passed', 'series_length', 'seed'
        ]

        for key in expected_keys:
            assert key in result, f"Missing key: {key}"


class TestSyntheticGenerationValidation:
    """Tests for comprehensive synthetic generation validation."""

    def test_white_noise_validation_passes(self, white_noise_series):
        """White noise should pass comprehensive validation."""
        passed, results = validate_synthetic_generation(
            white_noise_series,
            expected_h=0.5,
            n_shuffle_trials=100,
            seed=42
        )

        assert passed, f"White noise should pass validation: {results}"
        assert results['overall_passed']

    def test_validation_returns_expected_structure(self, white_noise_series):
        """Validation should return expected structure."""
        passed, results = validate_synthetic_generation(
            white_noise_series,
            expected_h=0.5,
            n_shuffle_trials=10,
            seed=42
        )

        assert isinstance(passed, bool)
        assert isinstance(results, dict)
        assert 'checks' in results
        assert 'series_length' in results
        assert 'overall_passed' in results


class TestValidateAllSyntheticSeries:
    """Tests for validating multiple synthetic series."""

    def test_multiple_series_validation(self):
        """Validate multiple series with different H values."""
        set_seed(42)
        rng = np.random.default_rng(42)

        # Create test series
        series_dict = {
            'white_noise': rng.standard_normal(500),
            'another_white': rng.standard_normal(500)
        }

        h_values = {
            'white_noise': 0.5,
            'another_white': 0.5
        }

        results = validate_all_synthetic_series(series_dict, h_values, seed=42)

        assert 'series_results' in results
        assert 'all_passed' in results
        assert 'failed_series' in results

        # Both should pass (white noise)
        assert results['all_passed'] or len(results['failed_series']) == 0

    def test_empty_dict(self):
        """Empty series dict should return valid structure."""
        results = validate_all_synthetic_series({}, {}, seed=42)

        assert results['all_passed']
        assert results['failed_series'] == []
        assert results['series_results'] == {}