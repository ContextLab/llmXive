"""
Unit tests for thermodynamic feature calculations.
"""
import pytest
import numpy as np
from code.features import (
    parse_composition,
    calculate_mixing_enthalpy,
    calculate_atomic_size_mismatch,
    calculate_electronegativity_variance,
)


def test_parse_composition_valid():
    """Test parsing a valid composition string."""
    composition_str = "Fe0.5Ni0.3Co0.2"
    expected = {"Fe": 0.5, "Ni": 0.3, "Co": 0.2}
    result = parse_composition(composition_str)
    assert result == expected


def test_parse_composition_invalid_format():
    """Test parsing an invalid composition string raises error."""
    # Testing format: missing element/fraction pattern
    with pytest.raises(ValueError):
        parse_composition("Fe0.5Ni0.3")


def test_parse_composition_sum_not_one():
    """Test that composition fractions must sum to 1.0."""
    with pytest.raises(ValueError):
        parse_composition("Fe0.5Ni0.2")  # Sum is 0.7


def test_calculate_mixing_enthalpy():
    """Test mixing enthalpy calculation for a simple ternary system."""
    composition = {"Fe": 0.5, "Ni": 0.3, "Co": 0.2}
    # Verify the function executes and returns a float for valid elements
    result = calculate_mixing_enthalpy(composition)
    assert isinstance(result, (float, np.floating))
    # The value should be a real number, not NaN or Inf for known elements
    assert not np.isnan(result)
    assert not np.isinf(result)


def test_calculate_atomic_size_mismatch():
    """Test atomic size mismatch calculation."""
    composition = {"Fe": 0.5, "Ni": 0.3, "Co": 0.2}
    result = calculate_atomic_size_mismatch(composition)
    assert isinstance(result, (float, np.floating))
    assert not np.isnan(result)
    assert not np.isinf(result)


def test_calculate_electronegativity_variance():
    """Test electronegativity variance calculation."""
    composition = {"Fe": 0.5, "Ni": 0.3, "Co": 0.2}
    result = calculate_electronegativity_variance(composition)
    assert isinstance(result, (float, np.floating))
    assert not np.isnan(result)
    assert not np.isinf(result)


def test_mixing_enthalpy_symmetry():
    """Test that mixing enthalpy is independent of element order."""
    comp1 = {"Fe": 0.5, "Ni": 0.3, "Co": 0.2}
    comp2 = {"Co": 0.2, "Fe": 0.5, "Ni": 0.3}
    result1 = calculate_mixing_enthalpy(comp1)
    result2 = calculate_mixing_enthalpy(comp2)
    assert np.isclose(result1, result2, rtol=1e-9)


def test_atomic_size_mismatch_symmetry():
    """Test that atomic size mismatch is independent of element order."""
    comp1 = {"Fe": 0.5, "Ni": 0.3, "Co": 0.2}
    comp2 = {"Co": 0.2, "Fe": 0.5, "Ni": 0.3}
    result1 = calculate_atomic_size_mismatch(comp1)
    result2 = calculate_atomic_size_mismatch(comp2)
    assert np.isclose(result1, result2, rtol=1e-9)


def test_electronegativity_variance_symmetry():
    """Test that electronegativity variance is independent of element order."""
    comp1 = {"Fe": 0.5, "Ni": 0.3, "Co": 0.2}
    comp2 = {"Co": 0.2, "Fe": 0.5, "Ni": 0.3}
    result1 = calculate_electronegativity_variance(comp1)
    result2 = calculate_electronegativity_variance(comp2)
    assert np.isclose(result1, result2, rtol=1e-9)


def test_parse_composition_element_case_sensitivity():
    """Test that element symbols are case-sensitive (e.g., 'fe' vs 'Fe')."""
    with pytest.raises(ValueError):
        parse_composition("fe0.5Ni0.3Co0.2")


def test_single_element_composition():
    """Test parsing a single element composition."""
    composition_str = "Fe1.0"
    expected = {"Fe": 1.0}
    result = parse_composition(composition_str)
    assert result == expected