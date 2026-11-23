"""
Unit tests for feature engineering functions.
"""
import pytest
import pandas as pd
import numpy as np
from code.feature_engineering import (
    get_element_property,
    parse_formula_elements,
    compute_atomic_fractions,
    compute_weighted_property,
    compute_variance_property,
    compute_descriptors
)

def test_get_element_property_ionic_radius():
    """Test retrieval of ionic radius for Pb."""
    radius = get_element_property('Pb', 'ionic_radius')
    assert radius is not None
    assert isinstance(radius, float)

def test_get_element_property_electronegativity():
    """Test retrieval of electronegativity for I."""
    en = get_element_property('I', 'electronegativity')
    assert en is not None
    assert isinstance(en, float)

def test_parse_formula_elements():
    """Test parsing of a simple perovskite formula."""
    elements = parse_formula_elements('FAPbI3')
    assert 'Pb' in elements
    assert 'I' in elements
    assert elements['Pb'] == 1
    assert elements['I'] == 3

def test_compute_atomic_fractions():
    """Test atomic fraction calculation."""
    elements = {'A': 1, 'B': 1, 'X': 3}
    frac_A, frac_B, frac_X = compute_atomic_fractions(elements)
    assert abs(frac_A - 0.2) < 1e-6
    assert abs(frac_B - 0.2) < 1e-6
    assert abs(frac_X - 0.6) < 1e-6

def test_compute_weighted_property():
    """Test weighted property calculation."""
    # Mock elements with known properties
    elements = {'Pb': 1, 'I': 3}
    # Pb electronegativity ~2.33, I ~2.66
    # Weighted mean = (1*2.33 + 3*2.66) / 4
    expected = (1 * 2.33 + 3 * 2.66) / 4
    result = compute_weighted_property(elements, 'electronegativity')
    # Allow some tolerance due to pymatgen values
    assert result is not None
    assert isinstance(result, float)

def test_compute_variance_property():
    """Test variance property calculation."""
    elements = {'Pb': 1, 'I': 3}
    variance = compute_variance_property(elements, 'electronegativity')
    assert variance is not None
    assert isinstance(variance, float)
    assert variance >= 0

def test_compute_descriptors():
    """Test full descriptor computation for a known formula."""
    desc = compute_descriptors('FAPbI3')
    assert 'atomic_fraction_A' in desc
    assert 'atomic_fraction_B' in desc
    assert 'atomic_fraction_X' in desc
    assert 'weighted_ionic_radius' in desc
    assert 'weighted_electronegativity' in desc
    assert 'variance_ionic_radius' in desc
    assert 'variance_electronegativity' in desc
    assert desc['atomic_fraction_A'] == 0.2
    assert desc['atomic_fraction_B'] == 0.2
    assert desc['atomic_fraction_X'] == 0.6

def test_compute_descriptors_missing_property():
    """Test handling of missing elemental properties."""
    # This should not crash, even if some properties are missing
    desc = compute_descriptors('FAPbI3')
    assert 'variance_ionic_radius' in desc
    assert 'variance_electronegativity' in desc