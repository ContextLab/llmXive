"""Unit tests for confidence interval computation.

The tests focus on the pure‑Python ``compute_confidence_interval`` helper.
They verify that the function returns a mean equal to the sample mean and
that the interval bounds are sensible (lower ≤ mean ≤ upper).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

# Import the function from the module we just created.
from code.analysis.confidence_intervals import compute_confidence_interval


@pytest.mark.parametrize(
    "data, confidence",
    [
        ([1.0, 2.0, 3.0, 4.0, 5.0], 0.95),
        (np.arange(10, dtype=float), 0.90),
        ([0.5, 0.5, 0.5, 0.5], 0.99),
    ],
)
def test_compute_confidence_interval_basic(data, confidence):
    """Check that the function returns a mean matching np.mean and sensible bounds."""
    mean, lower, upper = compute_confidence_interval(data, confidence=confidence)

    # The mean should be exactly the sample mean.
    expected_mean = float(np.mean(data))
    assert math.isclose(mean, expected_mean, rel_tol=1e-12)

    # Bounds must contain the mean.
    assert lower <= mean <= upper

    # For a non‑zero variance sample, the interval width should be > 0.
    if np.var(data) > 0:
        assert upper > lower
    else:
        # Zero variance → interval collapses to the mean.
        assert math.isclose(upper, lower, rel_tol=1e-12)


def test_compute_confidence_interval_empty():
    """An empty input should raise a ValueError."""
    with pytest.raises(ValueError, match="Data array is empty"):
        compute_confidence_interval([], confidence=0.95)