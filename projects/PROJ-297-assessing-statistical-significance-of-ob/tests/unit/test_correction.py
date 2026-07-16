"""Unit tests for the correction module."""
import pytest
import numpy as np
from correction import benjamini_yekutieli, apply_correction_to_results


def test_benjamini_yekutieli_known_values():
    """Test BY correction with known p-values."""
    p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
    q_values, is_significant = benjamini_yekutieli(p_values, alpha=0.05)

    # Check that q-values are monotonically increasing
    assert all(q_values[i] <= q_values[i+1] for i in range(len(q_values)-1))

    # Check that q-values are >= p-values
    assert all(q_values >= p_values)


def test_apply_correction_to_results():
    """Test applying correction to result dictionaries."""
    results = [
        {"p_value": 0.01},
        {"p_value": 0.02},
        {"p_value": 0.03},
    ]
    corrected = apply_correction_to_results(results, alpha=0.05)

    assert len(corrected) == 3
    assert all("q_value" in r for r in corrected)
    assert all("is_significant" in r for r in corrected)