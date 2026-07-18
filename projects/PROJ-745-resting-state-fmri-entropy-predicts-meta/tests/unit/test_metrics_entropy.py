"""
Unit tests for entropy calculation (T025).
Tests the multiscale sample entropy calculation using nolds.
"""

import numpy as np
import pytest
import logging

from code.metrics import calculate_multiscale_sample_entropy

logger = logging.getLogger(__name__)


def test_mse_random_data():
    """Test MSE calculation on random noise."""
    np.random.seed(42)
    ts = np.random.randn(500)

    results = calculate_multiscale_sample_entropy(ts)

    # Check that we got results for scales 1-5
    expected_scales = [1, 2, 3, 4, 5]
    for scale in expected_scales:
        assert scale in results, f"Scale {scale} missing from results"
        assert isinstance(results[scale], float), f"Result for scale {scale} is not a float"
        assert results[scale] >= 0, f"Entropy for scale {scale} is negative"


def test_mse_configurable_r():
    """Test that MSE respects the configurable r parameter."""
    np.random.seed(42)
    ts = np.random.randn(500)

    # Calculate with default r=0.15
    results_default = calculate_multiscale_sample_entropy(ts, r=0.15)
    # Calculate with custom r=0.20
    results_custom = calculate_multiscale_sample_entropy(ts, r=0.20)

    # Entropy values should differ when r changes
    # (Higher r usually leads to lower entropy)
    for scale in results_default:
        assert results_default[scale] != results_custom[scale], \
            f"Entropy for scale {scale} should differ with different r"


def test_mse_small_data():
    """Test MSE calculation on small time series (should handle gracefully)."""
    np.random.seed(42)
    ts = np.random.randn(50)

    # Should not crash, but might return fewer scales
    results = calculate_multiscale_sample_entropy(ts, scales=[1, 2])

    # At least scale 1 should work
    assert 1 in results or len(results) > 0, "Should get some results even for small data"


def test_mse_invalid_input():
    """Test MSE calculation with invalid input."""
    # Non-1D array
    with pytest.raises(ValueError):
        calculate_multiscale_sample_entropy(np.random.randn(10, 10))

    # Too many NaNs
    ts = np.random.randn(100)
    ts[20:30] = np.nan
    with pytest.raises(ValueError):
        calculate_multiscale_sample_entropy(ts, reject_outliers=True)

    # But should work if reject_outliers=False and we handle NaNs
    # (Our implementation interpolates, so it might work)
    # We test that it doesn't crash
    results = calculate_multiscale_sample_entropy(ts, reject_outliers=False)
    assert len(results) > 0, "Should handle some NaNs if reject_outliers=False"
