"""
Unit tests for meta-analysis calculation logic.
Verifies weighted mean and confidence intervals within specified tolerances.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add the project root to the path so we can import from code/
# This assumes the test is run from the project root or via pytest discovery
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.meta_analysis import run_random_effects_model, load_effect_sizes_and_se


def calculate_reference_weighted_mean(effect_sizes, sample_sizes, alpha=0.05):
    """
    Reference implementation for fixed-effect weighted mean using Fisher's Z.
    Used to verify the logic in run_random_effects_model.
    """
    effect_sizes = np.array(effect_sizes)
    sample_sizes = np.array(sample_sizes)

    # Clamp r to avoid domain errors in log
    r_clamped = np.clip(effect_sizes, -0.9999, 0.9999)

    # Fisher's Z transformation
    z = 0.5 * np.log((1 + r_clamped) / (1 - r_clamped))
    se_z = 1.0 / np.sqrt(sample_sizes - 3)

    # Weights (inverse variance)
    weights = 1.0 / (se_z ** 2)

    # Weighted mean in Z space
    weighted_mean_z = np.average(z, weights=weights)
    se_mean_z = np.sqrt(1.0 / np.sum(weights))

    # Critical value for 95% CI (approx 1.96 for large N)
    from scipy.stats import norm
    z_crit = norm.ppf(1 - alpha / 2)

    ci_lower_z = weighted_mean_z - z_crit * se_mean_z
    ci_upper_z = weighted_mean_z + z_crit * se_mean_z

    # Back-transform to r
    weighted_mean_r = (np.exp(2 * weighted_mean_z) - 1) / (np.exp(2 * weighted_mean_z) + 1)
    ci_lower_r = (np.exp(2 * ci_lower_z) - 1) / (np.exp(2 * ci_lower_z) + 1)
    ci_upper_r = (np.exp(2 * ci_upper_z) - 1) / (np.exp(2 * ci_upper_z) + 1)

    return weighted_mean_r, ci_lower_r, ci_upper_r


def test_weighted_mean_tolerance():
    """
    Verify weighted mean is within 0.001 tolerance of expected value.
    Tests the core calculation logic of run_random_effects_model.
    """
    # Setup: Three studies with known r and n
    # Study 1: r=0.8, n=103
    # Study 2: r=0.2, n=103
    # Study 3: r=0.2, n=103
    # Expected mean r (approx) for equal weights in Z-space: ~0.5767
    effects = [0.8, 0.2, 0.2]
    n_vals = [103, 103, 103]

    # Calculate reference values
    expected_mean, expected_lower, expected_upper = calculate_reference_weighted_mean(effects, n_vals)

    # Run the actual function from the module
    # Note: run_random_effects_model expects arrays and returns a dict
    result = run_random_effects_model(np.array(effects), np.array(n_vals))

    actual_mean = result['pooled_effect']

    # Assert within 0.001 tolerance
    assert abs(actual_mean - expected_mean) < 0.001, \
        f"Weighted mean mismatch: Expected {expected_mean:.6f}, got {actual_mean:.6f}"


def test_confidence_interval_calculation():
    """
    Verify that confidence intervals are calculated correctly and match reference.
    """
    effects = [0.5, 0.6, 0.4]
    n_vals = [100, 120, 110]

    expected_mean, expected_lower, expected_upper = calculate_reference_weighted_mean(effects, n_vals)

    result = run_random_effects_model(np.array(effects), np.array(n_vals))

    actual_lower = result['ci_lower']
    actual_upper = result['ci_upper']

    # Check CI bounds are reasonable (lower < mean < upper)
    assert actual_lower < result['pooled_effect'] < actual_upper

    # Check against reference (allowing small floating point differences)
    assert abs(actual_lower - expected_lower) < 0.01, \
        f"CI Lower mismatch: Expected {expected_lower:.4f}, got {actual_lower:.4f}"
    assert abs(actual_upper - expected_upper) < 0.01, \
        f"CI Upper mismatch: Expected {expected_upper:.4f}, got {actual_upper:.4f}"


def test_single_study():
    """
    Test behavior with a single study (edge case).
    """
    effects = [0.5]
    n_vals = [50]

    expected_mean, expected_lower, expected_upper = calculate_reference_weighted_mean(effects, n_vals)

    result = run_random_effects_model(np.array(effects), np.array(n_vals))

    # With one study, the pooled effect should be very close to the input
    assert abs(result['pooled_effect'] - effects[0]) < 0.01


def test_heterogeneity_estimation():
    """
    Test that the function returns heterogeneity metrics (tau^2, I^2).
    """
    effects = [0.1, 0.9, 0.5] # High variance
    n_vals = [100, 100, 100]

    result = run_random_effects_model(np.array(effects), np.array(n_vals))

    assert 'tau_squared' in result
    assert 'i_squared' in result
    assert result['tau_squared'] >= 0
    assert 0 <= result['i_squared'] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])