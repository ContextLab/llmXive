"""
Unit tests for the Hardy-Littlewood expected count calculation.
"""
import math
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from compute_expected_count import get_theoretical_count, HARDY_LITTLEWOOD_CONSTANT

def test_theoretical_count_formula():
    """
    Test the theoretical count calculation for a known small value.
    We can't easily verify exact counts for small x without a prime list,
    but we can verify the formula logic and that it returns a positive float.
    """
    limit = 100.0
    expected = get_theoretical_count(limit)
    assert expected > 0.0, "Expected count should be positive for limit > 2"
    
    # Check against the approximation formula: 2 * C2 * x / (ln x)^2
    log_x = math.log(limit)
    manual_calc = 2.0 * HARDY_LITTLEWOOD_CONSTANT * limit / (log_x * log_x)
    assert math.isclose(expected, manual_calc, rel_tol=1e-9), "Formula implementation mismatch"

def test_limit_boundary():
    """Test that count is 0 for limits <= 2."""
    assert get_theoretical_count(2.0) == 0.0
    assert get_theoretical_count(1.0) == 0.0
    assert get_theoretical_count(0.0) == 0.0

def test_limit_growth():
    """
    Verify that the theoretical count grows as limit increases.
    The function x/(ln x)^2 is increasing for x > e^2.
    """
    count_100 = get_theoretical_count(100.0)
    count_1000 = get_theoretical_count(1000.0)
    assert count_1000 > count_100, "Theoretical count should increase with limit"

def test_hardy_littlewood_constant():
    """Verify the constant is defined correctly."""
    # Known value approx 0.66016
    assert 0.66 < HARDY_LITTLEWOOD_CONSTANT < 0.67
    assert isinstance(HARDY_LITTLEWOOD_CONSTANT, float)