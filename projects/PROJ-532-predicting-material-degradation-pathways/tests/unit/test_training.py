"""
Unit test for the stratified split logic (task T021).

The test verifies that the ``stratified_split`` function is currently a
placeholder and raises ``NotImplementedError``. Once the real implementation
is added (in task T024), this test should be updated accordingly.
"""

import os
import sys

import pytest
import pandas as pd

# Ensure that the ``code`` directory is on the import path.
# This mirrors the project's intended PYTHONPATH configuration.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from training import stratified_split


def test_stratified_split_raises_not_implemented():
    """
    The placeholder implementation must raise ``NotImplementedError``.
    """
    # Minimal synthetic dataset
    X = pd.DataFrame(
        {
            "feature_a": [1, 2, 3, 4, 5, 6],
            "feature_b": [10, 20, 30, 40, 50, 60],
        }
    )
    y = pd.Series([0, 1, 0, 1, 0, 1])

    with pytest.raises(NotImplementedError):
        stratified_split(
            X,
            y,
            test_size=0.33,
            random_state=42,
        )