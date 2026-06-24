import pytest
import numpy as np

# Import the function from the project module
from analysis.statistical_tests import paired_t_test


def test_paired_t_test_identical_samples():
    """Identical samples should yield a t‑stat of 0 and p‑value of 1."""
    sample = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = paired_t_test(sample, sample)
    assert result["t_stat"] == pytest.approx(0.0, abs=1e-12)
    assert result["p_value"] == pytest.approx(1.0, abs=1e-12)
    assert result["df"] == 4.0  # len(sample) - 1


def test_paired_t_test_known_difference():
    """A simple case where one sample is uniformly higher should give a low p‑value."""
    sample1 = [1, 2, 3, 4, 5]
    sample2 = [2, 3, 4, 5, 6]  # each element +1
    result = paired_t_test(sample1, sample2)
    # The difference is constant, so t statistic is large in magnitude
    assert result["p_value"] < 0.001


def test_paired_t_test_mismatched_lengths():
    """Function should raise ValueError when input lengths differ."""
    with pytest.raises(ValueError):
        paired_t_test([1, 2, 3], [1, 2])
