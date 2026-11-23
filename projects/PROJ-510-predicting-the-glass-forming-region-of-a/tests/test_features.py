"""
Unit tests for feature engineering functions.
"""
import pytest
import math
from code.features import (
    parse_composition_to_dict,
    calculate_mixing_enthalpy,
    calculate_atomic_size_mismatch,
    calculate_electronegativity_variance
)

def test_parse_composition_simple():
    """Test basic composition parsing."""
    comp_str = "Al40Cu30Zr30"
    result = parse_composition_to_dict(comp_str)
    assert abs(result['Al'] - 0.4) < 1e-5
    assert abs(result['Cu'] - 0.3) < 1e-5
    assert abs(result['Zr'] - 0.3) < 1e-5

def test_parse_composition_floats():
    """Test parsing with float percentages."""
    comp_str = "Al33.33Cu33.33Zr33.34"
    result = parse_composition_to_dict(comp_str)
    assert abs(result['Al'] - 0.3333) < 1e-3
    assert abs(result['Cu'] - 0.3333) < 1e-3
    assert abs(result['Zr'] - 0.3334) < 1e-3

def test_parse_composition_invalid():
    """Test parsing with invalid element."""
    comp_str = "Xy40Cu30Zr30"
    result = parse_composition_to_dict(comp_str)
    # Xy is not a real element, so it should be skipped
    assert 'Xy' not in result
    assert len(result) == 2 # Cu and Zr only

def test_calc_mixing_enthalpy_known():
    """Test mixing enthalpy with known coefficients."""
    # Al40Cu30Zr30 -> Al-Cu, Al-Zr, Cu-Zr
    # Coeffs: Al-Cu: -36, Al-Zr: -40, Cu-Zr: -24
    # H = 0.4*0.3*(-36) + 0.4*0.3*(-40) + 0.3*0.3*(-24)
    #   = 0.12*(-36) + 0.12*(-40) + 0.09*(-24)
    #   = -4.32 - 4.8 - 2.16 = -11.28
    comp = {'Al': 0.4, 'Cu': 0.3, 'Zr': 0.3}
    result = calculate_mixing_enthalpy(comp)
    expected = 0.4*0.3*(-36) + 0.4*0.3*(-40) + 0.3*0.3*(-24)
    assert abs(result - expected) < 1e-3

def test_calc_size_mismatch():
    """Test atomic size mismatch calculation."""
    # Use a known case or just verify it returns a float
    comp = {'Al': 0.33, 'Cu': 0.33, 'Zr': 0.34}
    result = calculate_atomic_size_mismatch(comp)
    assert isinstance(result, float)
    assert result >= 0

def test_calc_electronegativity_variance():
    """Test electronegativity variance calculation."""
    comp = {'Al': 0.33, 'Cu': 0.33, 'Zr': 0.34}
    result = calculate_electronegativity_variance(comp)
    assert isinstance(result, float)
    assert result >= 0
