"""
Unit tests for the ``bug_detection`` module.

The only behaviour required for the current test suite is the
``compute_pass1_accuracy`` function, which must correctly calculate the
proportion of True values in an iterable.
"""

import pandas as pd
import pytest

from bug_detection import compute_pass1_accuracy

def test_compute_pass1_accuracy_basic():
    # Simple three‑element case – two successes, one failure → 2/3
    df = pd.DataFrame({"passed": [True, False, True]})
    acc = compute_pass1_accuracy(df["passed"])
    assert acc == pytest.approx(2 / 3)

def test_compute_pass1_accuracy_all_true():
    df = pd.DataFrame({"passed": [True, True, True, True]})
    acc = compute_pass1_accuracy(df["passed"])
    assert acc == pytest.approx(1.0)

def test_compute_pass1_accuracy_all_false():
    df = pd.DataFrame({"passed": [False, False]})
    acc = compute_pass1_accuracy(df["passed"])
    assert acc == pytest.approx(0.0)

def test_compute_pass1_accuracy_empty_raises():
    with pytest.raises(ValueError):
        compute_pass1_accuracy([])
