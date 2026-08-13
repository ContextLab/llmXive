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
