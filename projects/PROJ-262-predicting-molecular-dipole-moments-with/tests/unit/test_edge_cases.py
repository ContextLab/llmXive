import pytest
import numpy as np

from analysis.confidence_intervals import compute_confidence_interval
from training.evaluate import mae, rmse
from analysis.statistical_tests import paired_t_test
from utils.validate_urls import check_url


def test_compute_confidence_interval_known():
    """
    Basic sanity check: the confidence interval should contain the mean of the data
    and have a positive width.
    """
    data = [1, 2, 3, 4, 5]
    lower, upper = compute_confidence_interval(data, confidence=0.95)
    # The mean of the data is 3.0; the interval should surround it.
    assert lower < 3.0 < upper
    # Width must be positive.
    assert upper > lower


def test_mae_and_rmse_basic():
    """Exact predictions should yield zero error."""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    assert mae(y_true, y_pred) == 0.0
    assert rmse(y_true, y_pred) == 0.0


def test_mae_mismatched_lengths():
    """MAE should raise a ValueError when input lengths differ."""
    y_true = np.array([1.0, 2.0])
    y_pred = np.array([1.0])
    with pytest.raises(ValueError):
        mae(y_true, y_pred)


def test_paired_t_test_identical():
    """Identical samples give a t-statistic of 0 and a p-value of 1."""
    a = np.array([1, 2, 3, 4])
    b = np.array([1, 2, 3, 4])
    t_stat, p_val = paired_t_test(a, b)
    assert np.isclose(t_stat, 0.0)
    assert np.isclose(p_val, 1.0)


def test_check_url_invalid():
    """
    An obviously malformed URL should be reported as invalid.
    The implementation returns a boolean, so we assert a falsy result.
    """
    assert not check_url("not a valid url")