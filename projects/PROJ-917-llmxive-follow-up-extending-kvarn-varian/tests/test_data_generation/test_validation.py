"""
Unit tests for data validation logic.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_generation.utils import check_numerical_stability


def test_validation_pass():
    """Test that valid data passes validation."""
    assert check_numerical_stability(1.0) is True
    assert check_numerical_stability(0.0) is True
    assert check_numerical_stability(1e-6) is True


def test_validation_fail_nan():
    """Test that NaN values fail validation."""
    assert check_numerical_stability(np.nan) is False


def test_validation_fail_inf():
    """Test that Inf values fail validation."""
    assert check_numerical_stability(np.inf) is False
    assert check_numerical_stability(-np.inf) is False