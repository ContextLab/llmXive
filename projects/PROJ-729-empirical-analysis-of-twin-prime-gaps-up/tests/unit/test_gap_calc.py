"""
Unit tests for gap calculation logic.
"""
import math
import pytest

def test_normalized_gap_formula():
    """
    Verify formula `delta / log(p)` equals expected float 1.8205 for input p=3, p_next=5.
    Verification: Use tolerance `assert abs(val - 1.8205) < 1e-4` to handle floating point precision.
    """
    p = 3
    p_next = 5
    delta = p_next - p
    
    # Calculate normalized gap
    # Note: log(p) uses natural logarithm in math module
    val = delta / math.log(p)
    
    expected = 1.8205
    tolerance = 1e-4
    
    assert abs(val - expected) < tolerance, f"Expected {expected}, got {val} (diff: {abs(val - expected)})"
