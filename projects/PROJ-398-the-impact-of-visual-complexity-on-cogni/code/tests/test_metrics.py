"""
Unit tests for correlation calculation in the pilot gate module.

This test verifies that the ``compute_correlation`` function from
``src.experiment.pilot_gate`` correctly computes the Pearson correlation
coefficient and associated p‑value for two perfectly correlated series.
"""

import pytest
import pandas as pd

# Import the function under test
from src.experiment.pilot_gate import compute_correlation


def test_correlation_calculation():
    """
    Create two perfectly linearly related series and ensure the
    correlation coefficient is exactly 1.0 (within a tolerance) and that
    the p‑value indicates statistical significance.
    """
    # Perfect linear relationship: y = 2 * x
    x = pd.Series([1, 2, 3, 4, 5])
    y = pd.Series([2, 4, 6, 8, 10])

    r, p_value = compute_correlation(x, y)

    # Pearson correlation for a perfect linear relationship should be 1.0
    assert pytest.approx(r, rel=1e-6) == 1.0

    # The p‑value for a perfect correlation with 5 samples should be
    # very small (statistically significant)
    assert p_value < 0.001