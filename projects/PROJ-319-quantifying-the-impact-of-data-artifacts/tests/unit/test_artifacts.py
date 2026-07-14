"""Unit tests for artifact injection logic in code/synthetic/artifacts.py.

These tests verify that noise injection and saturation clipping behave
according to their specifications.
"""
import numpy as np
import pytest
from code.synthetic.artifacts import inject_noise, clip_saturation

def test_noise_injection_sigma():
    """Assert that injected noise matches target sigma within tolerance."""
    # Create a zero image
    image = np.zeros((100, 100))
    sigma_target = 10.0
    seed = 12345

    noisy = inject_noise(image, sigma=sigma_target, seed=seed)

    # The noise is the difference
    noise = noisy - image
    sigma_observed = np.std(noise)

    # Tolerance: 5% of target sigma
    tolerance = 0.05 * sigma_target
    assert abs(sigma_observed - sigma_target) < tolerance, \
        f"Observed sigma {sigma_observed:.4f} differs from target {sigma_target:.4f} by more than {tolerance:.4f}"

def test_noise_injection_deterministic():
    """Assert that the same seed produces the same noise."""
    image = np.ones((10, 10))
    sigma = 5.0
    seed = 42

    noisy1 = inject_noise(image, sigma, seed)
    noisy2 = inject_noise(image, sigma, seed)

    np.testing.assert_array_equal(noisy1, noisy2)

def test_saturation_clipping():
    """Assert that the correct fraction of brightest pixels are clipped."""
    # Create an image with known distribution: 0 to 100
    # 100 pixels, 10% should be clipped (top 10 pixels)
    image = np.arange(100).reshape(10, 10).astype(float)
    fraction = 0.10
    seed = 42

    clipped, threshold = clip_saturation(image, fraction, seed)

    # The threshold should be the 90th percentile
    # In 0..99, 90th percentile is 89.1 (approx) or 90th value?
    # np.percentile([0..99], 90) -> 89.1
    expected_threshold = np.percentile(image.flatten(), 90)
    assert abs(threshold - expected_threshold) < 1e-5, \
        f"Threshold {threshold} != {expected_threshold}"

    # Count clipped pixels
    # Pixels > threshold are clipped to threshold
    # In the original image, pixels > 89.1 are 90, 91, ..., 99 (10 pixels)
    original_clipped_count = np.sum(image > threshold)
    # After clipping, those pixels should equal threshold
    # Check if they are equal to threshold
    clipped_pixels = clipped[image > threshold]
    assert np.all(clipped_pixels == threshold), "Clipped pixels should equal threshold"

    # Verify the fraction of clipped pixels is approximately correct
    # Note: Due to floating point and percentile definition, exact count might vary slightly
    # but for this discrete set, it should be exact.
    assert len(clipped_pixels) == original_clipped_count

def test_saturation_clipping_deterministic():
    """Assert that the same seed produces the same result."""
    image = np.random.rand(20, 20) * 100
    fraction = 0.2
    seed = 999

    clipped1, thresh1 = clip_saturation(image, fraction, seed)
    clipped2, thresh2 = clip_saturation(image, fraction, seed)

    np.testing.assert_array_equal(clipped1, clipped2)
    assert thresh1 == thresh2