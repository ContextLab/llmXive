"""
tests/unit/test_descriptors.py

Unit tests for descriptor calculations.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.descriptors import calculate_tolerance_factor, get_ionic_radius

def test_tolerance_factor_calculation_returns_correct_value_for_BaTiO3():
    """
    Test tolerance factor calculation for BaTiO3.
    Formula: t = (r_A + r_X) / (sqrt(2) * (r_B + r_X))
    
    Expected values for BaTiO3:
    r_Ba (12-coord) ~ 1.61 A
    r_Ti (6-coord) ~ 0.605 A
    r_O (6-coord) ~ 1.40 A
    
    t = (1.61 + 1.40) / (sqrt(2) * (0.605 + 1.40))
    t = 3.01 / (1.414 * 2.005)
    t = 3.01 / 2.835
    t ≈ 1.06
    """
    # Ionic radii in Angstroms (Shannon radii for appropriate coordination)
    r_Ba = 1.61  # Ba2+ in 12-coordination
    r_Ti = 0.605 # Ti4+ in 6-coordination
    r_O = 1.40   # O2- in 6-coordination

    t = calculate_tolerance_factor(r_Ba, r_Ti, r_O)
    
    expected = (r_Ba + r_O) / (2**0.5 * (r_Ti + r_O))
    
    # Assert with tolerance of 0.01 to account for minor radius variations
    assert abs(t - 1.06) < 0.01, f"Calculated {t}, expected approx 1.06"
    assert abs(t - expected) < 1e-6, f"Calculated {t}, expected {expected}"

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