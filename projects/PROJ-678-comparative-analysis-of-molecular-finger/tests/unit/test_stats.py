"""
Unit tests for statistical utilities related to K-Fold scores.
Specifically tests the corrected resampled t-test (Nadeau & Bengio)
implementation used to compare Morgan vs MACCS ROC‑AUC scores.
"""

import numpy as np
import pytest

# Import the helper function that implements the corrected resampled t‑test.
# The helper is located in ``code/evaluate_helper.py`` to keep the original
# ``code/evaluate.py`` untouched.
from evaluate_helper import perform_corrected_resampled_ttest


@pytest.mark.parametrize(
    "scores_a, scores_b, n_folds, expected_min_p",
    [
        # Identical scores → no difference, p‑value should be close to 1.
        (
            [0.78, 0.80, 0.79, 0.77, 0.81],
            [0.78, 0.80, 0.79, 0.77, 0.81],
            5,
            0.9,
        ),
        # Small systematic advantage for model A.
        (
            [0.82, 0.84, 0.83, 0.81, 0.85],
            [0.78, 0.80, 0.79, 0.77, 0.81],
            5,
            0.05,  # Expect a statistically significant advantage (p < 0.05)
        ),
    ],
)
def test_paired_ttest_cv_scores(scores_a, scores_b, n_folds, expected_min_p):
    """
    Verify that the corrected resampled t‑test returns sensible p‑values.

    * When the two score vectors are identical the p‑value must be
      large (close to 1).
    * When there is a clear performance gap the p‑value must be small
      (below the ``expected_min_p`` threshold supplied by the test case).
    """
    p_value = perform_corrected_resampled_ttest(
        scores_a=scores_a,
        scores_b=scores_b,
        n_folds=n_folds,
    )

    # ``p_value`` should be a float between 0 and 1.
    assert 0.0 <= p_value <= 1.0, "p‑value out of bounds"

    if np.allclose(scores_a, scores_b):
        # No difference → p‑value should be high.
        assert p_value > expected_min_p
    else:
        # Detect a statistically significant difference.
        assert p_value < expected_min_p


def test_bootstrap_confidence_interval():
    """
    Verify bootstrap confidence interval calculation.
    
    This test checks that the bootstrap function:
    1. Returns a tuple of (lower, upper) bounds.
    2. The lower bound is less than or equal to the upper bound.
    3. The confidence interval contains the true mean difference when
       the sample size is large and the distribution is normal.
    4. The function is deterministic with a fixed random seed.
    """
    from evaluate import compute_bootstrap_confidence_interval

    # Generate synthetic but realistic K-Fold ROC-AUC score differences
    # Morgan - MACCS differences (simulating a scenario where Morgan is slightly better)
    np.random.seed(42)
    n_iterations = 1000
    n_folds = 5
    
    # Create a set of differences that follows a normal distribution
    # Mean difference ~ 0.05, std ~ 0.02
    true_diffs = np.random.normal(loc=0.05, scale=0.02, size=n_folds)
    
    # Run bootstrap with fixed seed for reproducibility
    lower, upper = compute_bootstrap_confidence_interval(
        diffs=true_diffs,
        n_iterations=n_iterations,
        confidence_level=0.95,
        random_seed=42
    )
    
    # Verify return type and structure
    assert isinstance(lower, float), "Lower bound must be a float"
    assert isinstance(upper, float), "Upper bound must be a float"
    assert lower <= upper, "Lower bound must be less than or equal to upper bound"
    
    # Verify the confidence interval captures the true mean difference
    # (This is a probabilistic check - with 95% CI, it should capture ~95% of the time)
    true_mean_diff = np.mean(true_diffs)
    assert lower <= true_mean_diff <= upper, \
        f"95% CI [{lower:.4f}, {upper:.4f}] should contain true mean {true_mean_diff:.4f}"
    
    # Test determinism: running with the same seed should produce identical results
    lower2, upper2 = compute_bootstrap_confidence_interval(
        diffs=true_diffs,
        n_iterations=n_iterations,
        confidence_level=0.95,
        random_seed=42
    )
    assert np.isclose(lower, lower2), "Bootstrap results should be deterministic with same seed"
    assert np.isclose(upper, upper2), "Bootstrap results should be deterministic with same seed"
    
    # Test with edge case: all differences are zero
    zero_diffs = np.zeros(n_folds)
    lower_zero, upper_zero = compute_bootstrap_confidence_interval(
        diffs=zero_diffs,
        n_iterations=100,
        confidence_level=0.95,
        random_seed=42
    )
    assert np.isclose(lower_zero, 0.0, atol=0.01), \
        f"CI for zero differences should be near zero, got [{lower_zero:.4f}, {upper_zero:.4f}]"
    assert np.isclose(upper_zero, 0.0, atol=0.01), \
        f"CI for zero differences should be near zero, got [{lower_zero:.4f}, {upper_zero:.4f}]"
    
    # Test with different confidence levels
    lower_90, upper_90 = compute_bootstrap_confidence_interval(
        diffs=true_diffs,
        n_iterations=1000,
        confidence_level=0.90,
        random_seed=42
    )
    lower_99, upper_99 = compute_bootstrap_confidence_interval(
        diffs=true_diffs,
        n_iterations=1000,
        confidence_level=0.99,
        random_seed=42
    )
    
    # 99% CI should be wider than 90% CI
    width_90 = upper_90 - lower_90
    width_99 = upper_99 - lower_99
    assert width_99 >= width_90, \
        f"99% CI width ({width_99:.4f}) should be >= 90% CI width ({width_90:.4f})"