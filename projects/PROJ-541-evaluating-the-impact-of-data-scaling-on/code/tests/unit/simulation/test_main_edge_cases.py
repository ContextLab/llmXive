"""
Additional edge case tests for main.py iteration enforcement.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import enforce_iteration_threshold


def test_zero_iterations():
    """Test enforcement with zero requested iterations."""
    result = enforce_iteration_threshold(0)
    assert result == 10000


def test_negative_iterations():
    """Test enforcement with negative requested iterations."""
    result = enforce_iteration_threshold(-100)
    assert result == 10000


def test_just_under_threshold():
    """Test enforcement with iterations just under the threshold."""
    result = enforce_iteration_threshold(9999)
    assert result == 10000


def test_just_over_threshold():
    """Test enforcement with iterations just over the threshold."""
    result = enforce_iteration_threshold(10001)
    assert result == 10001
