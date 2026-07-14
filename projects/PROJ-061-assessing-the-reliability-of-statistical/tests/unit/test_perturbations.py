"""
Unit tests for perturbation functions (US2).
Tests the logic for inducing assumption violations: heavy-tailed noise, AR(1), and effect size heterogeneity.
"""
import pytest
import numpy as np
from scipy import stats

# Import the functions to be tested from the sibling module
# The implementation is expected to be in code/perturbations.py (T021)
try:
    from perturbations import (
        inject_heavy_tailed_noise,
        inject_ar1_autocorrelation,
        verify_ar1_coefficient,
        inject_effect_size_heterogeneity
    )
except ImportError:
    # If the module doesn't exist yet, skip tests gracefully to allow the test suite
    # to run other tests. This is expected for TDD when implementation is pending.
    pytest.skip("perturbations module not yet implemented (T021 pending)", allow_module_level=True)


# --- Heavy-Tailed Noise Tests ---

def test_heavy_tailed_injection_kurtosis_increase():
    """
    Test that heavy-tailed noise injection increases kurtosis significantly.
    """
    np.random.seed(42)
    n_samples = 2000
    contamination_rate = 0.1
    df = 3.0  # Low degrees of freedom for heavy tails

    # Generate normal base data
    base_data = np.random.normal(loc=0, scale=1, size=n_samples)

    # Inject heavy tails
    perturbed_data = inject_heavy_tailed_noise(
        base_data,
        contamination_rate=contamination_rate,
        df=df
    )

    # Calculate kurtosis (excess kurtosis for normal is 0)
    base_kurtosis = stats.kurtosis(base_data, fisher=True)
    perturbed_kurtosis = stats.kurtosis(perturbed_data, fisher=True)

    # Heavy tails should result in significantly higher excess kurtosis
    assert perturbed_kurtosis > base_kurtosis, \
        f"Perturbed kurtosis ({perturbed_kurtosis:.2f}) should be higher than base ({base_kurtosis:.2f})"
    assert perturbed_kurtosis > 2.0, \
        f"Expected high kurtosis (>2.0) for heavy-tailed data, got {perturbed_kurtosis:.2f}"


def test_heavy_tailed_injection_preserves_mean_approx():
    """
    Test that mean is approximately preserved (symmetric heavy tails).
    """
    np.random.seed(123)
    n_samples = 5000
    base_data = np.random.normal(loc=5.0, scale=1.0, size=n_samples)

    perturbed_data = inject_heavy_tailed_noise(base_data, contamination_rate=0.1, df=4.0)

    # Means should be close, allowing for sampling variance from heavy tails
    np.testing.assert_almost_equal(np.mean(perturbed_data), np.mean(base_data), decimal=0)


# --- AR(1) Autocorrelation Tests (Existing + Expanded) ---

def test_ar1_injection_autocorrelation_present():
    """
    Test that AR(1) injection successfully introduces positive autocorrelation.
    """
    np.random.seed(42)
    n_samples = 1000
    target_rho = 0.6

    # Generate white noise (uncorrelated)
    base_data = np.random.normal(loc=0, scale=1, size=n_samples)

    # Inject AR(1)
    perturbed_data = inject_ar1_autocorrelation(base_data, ar_coefficient=target_rho)

    # Verify autocorrelation
    passed, achieved_rho = verify_ar1_coefficient(perturbed_data, target_rho, tolerance=0.05)

    assert passed, f"ACHIEVED: {achieved_rho:.3f}, TARGET: {target_rho}. Tolerance: 0.05"
    assert achieved_rho > 0.0, "Autocorrelation should be positive"


def test_ar1_injection_negative_autocorrelation():
    """
    Test that AR(1) injection works for negative autocorrelation.
    """
    np.random.seed(123)
    n_samples = 1000
    target_rho = -0.5

    base_data = np.random.normal(loc=0, scale=1, size=n_samples)
    perturbed_data = inject_ar1_autocorrelation(base_data, ar_coefficient=target_rho)

    passed, achieved_rho = verify_ar1_coefficient(perturbed_data, target_rho, tolerance=0.05)

    assert passed, f"ACHIEVED: {achieved_rho:.3f}, TARGET: {target_rho}. Tolerance: 0.05"
    assert achieved_rho < 0.0, "Autocorrelation should be negative"


def test_ar1_injection_preserves_mean_variance():
    """
    Test that AR(1) injection preserves the approximate mean and variance of the original data.
    The transformation scales to match the original stats.
    """
    np.random.seed(999)
    n_samples = 10000
    target_rho = 0.5

    base_data = np.random.normal(loc=5.0, scale=2.0, size=n_samples)
    perturbed_data = inject_ar1_autocorrelation(base_data, ar_coefficient=target_rho)

    # Check mean (should be very close)
    np.testing.assert_almost_equal(np.mean(perturbed_data), np.mean(base_data), decimal=1)

    # Check variance (should be close, small sampling variance expected)
    # We allow a 20% tolerance due to sampling noise in finite samples
    base_var = np.var(base_data)
    perturbed_var = np.var(perturbed_data)
    ratio = perturbed_var / base_var
    assert 0.8 <= ratio <= 1.2, f"Variance ratio {ratio:.2f} is outside acceptable range [0.8, 1.2]"


def test_ar1_injection_invalid_coefficient():
    """
    Test that invalid AR coefficients raise an error.
    """
    np.random.seed(42)
    base_data = np.random.normal(size=100)

    with pytest.raises(ValueError):
        inject_ar1_autocorrelation(base_data, ar_coefficient=1.5)

    with pytest.raises(ValueError):
        inject_ar1_autocorrelation(base_data, ar_coefficient=-1.5)


def test_ar1_injection_deterministic_with_seed():
    """
    Test that the function produces deterministic results with a fixed random seed.
    """
    base_data = np.random.normal(loc=0, scale=1, size=100)

    np.random.seed(888)
    result1 = inject_ar1_autocorrelation(base_data, ar_coefficient=0.5, seed=123)

    np.random.seed(888)
    result2 = inject_ar1_autocorrelation(base_data, ar_coefficient=0.5, seed=123)

    np.testing.assert_array_equal(result1, result2,
        "Results should be identical with the same random seed")

def test_ar1_injection_short_data():
    """
    Test behavior with very short data (edge case).
    """
    short_data = np.array([1.0, 2.0])
    result = inject_ar1_autocorrelation(short_data, ar_coefficient=0.5)
    assert len(result) == 2
    assert np.allclose(result, short_data) # Should return copy if too short to meaningfully transform


# --- Effect Size Heterogeneity Tests (T019) ---

def test_heterogeneity_injection_creates_subpopulations():
    """
    Test that effect size heterogeneity injection creates a mixture of two sub-populations.
    Verifies the mixing ratio and separation distance.
    """
    np.random.seed(42)
    n_samples = 2000
    mixing_ratio = 0.2
    separation_distance = 1.5  # Standard deviations
    base_mean = 0.0
    base_std = 1.0

    # Generate homogeneous base data
    base_data = np.random.normal(loc=base_mean, scale=base_std, size=n_samples)

    # Inject heterogeneity
    perturbed_data = inject_effect_size_heterogeneity(
        base_data,
        mixing_ratio=mixing_ratio,
        separation_distance=separation_distance,
        seed=42
    )

    # The perturbed data should now have a different distribution
    # Specifically, we expect a shift in the mean due to the injected sub-population
    # The injected group (20%) has mean = base_mean + (separation_distance * base_std)
    # Expected new mean = (1 - 0.2)*0 + 0.2*(0 + 1.5*1) = 0.3
    expected_mean_shift = (1 - mixing_ratio) * base_mean + mixing_ratio * (base_mean + separation_distance * base_std)
    
    # Check that the mean has shifted significantly
    assert not np.isclose(np.mean(perturbed_data), np.mean(base_data)), \
        "Mean should have shifted due to heterogeneity injection"
    
    # Allow for some sampling variance
    assert abs(np.mean(perturbed_data) - expected_mean_shift) < 0.15, \
        f"Mean {np.mean(perturbed_data):.2f} is far from expected {expected_mean_shift:.2f}"


def test_heterogeneity_injection_increases_variance():
    """
    Test that injecting a sub-population with a different mean increases total variance.
    """
    np.random.seed(123)
    n_samples = 5000
    mixing_ratio = 0.2
    separation_distance = 1.5

    base_data = np.random.normal(loc=0, scale=1.0, size=n_samples)
    perturbed_data = inject_effect_size_heterogeneity(
        base_data,
        mixing_ratio=mixing_ratio,
        separation_distance=separation_distance,
        seed=123
    )

    base_var = np.var(base_data)
    perturbed_var = np.var(perturbed_data)

    # Variance should increase significantly because we added a shifted component
    assert perturbed_var > base_var, \
        f"Variance should increase. Base: {base_var:.2f}, Perturbed: {perturbed_var:.2f}"
    
    # Theoretical variance of mixture:
    # Var = (1-p)*Var1 + p*Var2 + p*(1-p)*(mu1-mu2)^2
    # Assuming Var1=Var2=1, p=0.2, diff=1.5
    # Var = 0.8*1 + 0.2*1 + 0.2*0.8*(1.5)^2 = 1 + 0.16*2.25 = 1 + 0.36 = 1.36
    # We expect perturbed_var to be roughly around 1.36
    assert perturbed_var > 1.2, f"Variance {perturbed_var:.2f} is too low for expected mixture"


def test_heterogeneity_injection_deterministic_with_seed():
    """
    Test that the function produces deterministic results with a fixed random seed.
    """
    base_data = np.random.normal(loc=0, scale=1, size=100)

    np.random.seed(888)
    result1 = inject_effect_size_heterogeneity(
        base_data, 
        mixing_ratio=0.2, 
        separation_distance=1.5, 
        seed=123
    )

    np.random.seed(888)
    result2 = inject_effect_size_heterogeneity(
        base_data, 
        mixing_ratio=0.2, 
        separation_distance=1.5, 
        seed=123
    )

    np.testing.assert_array_equal(result1, result2,
        "Results should be identical with the same random seed")


def test_heterogeneity_injection_invalid_mixing_ratio():
    """
    Test that invalid mixing ratios raise an error.
    """
    base_data = np.random.normal(size=100)

    with pytest.raises(ValueError):
        inject_effect_size_heterogeneity(base_data, mixing_ratio=1.5, separation_distance=1.0)

    with pytest.raises(ValueError):
        inject_effect_size_heterogeneity(base_data, mixing_ratio=-0.1, separation_distance=1.0)


def test_heterogeneity_injection_preserves_sample_size():
    """
    Test that the output array has the same length as the input.
    """
    np.random.seed(42)
    n_samples = 500
    base_data = np.random.normal(size=n_samples)

    perturbed_data = inject_effect_size_heterogeneity(
        base_data, 
        mixing_ratio=0.2, 
        separation_distance=1.5
    )

    assert len(perturbed_data) == n_samples, \
        f"Output length {len(perturbed_data)} does not match input {n_samples}"

def test_heterogeneity_injection_edge_case_zero_separation():
    """
    Test behavior when separation distance is 0 (should effectively be no change).
    """
    np.random.seed(42)
    n_samples = 100
    base_data = np.random.normal(size=n_samples)

    result = inject_effect_size_heterogeneity(
        base_data, 
        mixing_ratio=0.5, 
        separation_distance=0.0
    )

    # If separation is 0, the sub-population has the same mean as the base.
    # Theoretically, the distribution should be identical to the base (within sampling noise).
    # However, the implementation might still add noise if it simulates a different variance.
    # Assuming standard implementation: same mean, same variance -> identical distribution.
    # We check that the mean is preserved.
    assert np.isclose(np.mean(result), np.mean(base_data), atol=0.1), \
        "Mean should be preserved when separation is 0"