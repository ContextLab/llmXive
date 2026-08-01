"""
tests/unit/test_descriptors.py

Unit tests for descriptor calculations.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.descriptors import calculate_tolerance_factor, get_ionic_radius

def test_tolerance_factor_calculation_returns_correct_value_for_KCl3():
    """
    Test tolerance factor calculation for KCl3 (hypothetical perovskite example).
    Formula: t = (r_A + r_X) / (sqrt(2) * (r_B + r_X))
    """
    # Mock radii for K, Cl (assuming B is Cl for this test case, or adjust as needed)
    # Real radii: K+ ~ 1.38 A, Cl- ~ 1.81 A
    # If KCl3 is A=K, B=Cl, X=Cl? No, usually ABX3.
    # Let's assume a hypothetical case: A=K, B=Ti, X=Cl.
    # We test the function logic directly with known values.
    
    r_A = 1.38 # K
    r_B = 0.605 # Ti
    r_X = 1.81 # Cl

    t = calculate_tolerance_factor(r_A, r_B, r_X)
    
    # Expected: (1.38 + 1.81) / (sqrt(2) * (0.605 + 1.81))
    # = 3.19 / (1.414 * 2.415) = 3.19 / 3.415 = 0.934
    
    expected = (r_A + r_X) / (2**0.5 * (r_B + r_X))
    
    assert abs(t - expected) < 1e-6, f"Calculated {t}, expected {expected}"

def test_get_ionic_radius_returns_value():
    """Test that ionic radius lookup returns a value for known elements."""
    r = get_ionic_radius("K", "+1")
    assert r is not None
    assert r > 0
