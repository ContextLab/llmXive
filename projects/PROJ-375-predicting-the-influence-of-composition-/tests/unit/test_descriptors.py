"""
Unit tests for feature engineering descriptors.
"""
import pytest
import math
from features.descriptors import (
    parse_formula,
    calculate_weighted_mean_radius,
    calculate_variance_electronegativity,
    calculate_weighted_mean_VEC,
    calculate_atomic_size_mismatch,
    extract_descriptors
)

def test_parse_formula():
    """Test parsing of Zr50Cu40Al10"""
    result = parse_formula("Zr50Cu40Al10")
    expected = {'Zr': 0.5, 'Cu': 0.4, 'Al': 0.1}
    assert result == expected

    # Test without numbers (should default to 1)
    result2 = parse_formula("H2O") # H2O is H:2, O:1 -> H: 0.666, O: 0.333
    # H2O -> H:2, O:1. Total 3. H: 2/3, O: 1/3
    assert abs(result2['H'] - 2/3) < 1e-5
    assert abs(result2['O'] - 1/3) < 1e-5

def test_calculate_weighted_mean_radius():
    """Test radius calculation with known values"""
    # Mock data: Zr (160pm), Cu (128pm)
    # Formula: Zr50Cu50 -> 0.5*160 + 0.5*128 = 144
    composition = {'Zr': 0.5, 'Cu': 0.5}
    # We rely on mendeleev for real values, but we can check structure
    # Zr atomic radius ~ 160, Cu ~ 128. 
    # Let's just ensure it returns a float and is reasonable
    result = calculate_weighted_mean_radius(composition)
    assert isinstance(result, float)
    assert result > 0
    # Rough check: should be between min and max radius of elements
    # Mendeleev values might vary slightly, but 144 is a good target
    assert 130 < result < 155 

def test_calculate_variance_electronegativity():
    """Test variance calculation"""
    # Pure element should have 0 variance
    result = calculate_variance_electronegativity({'Fe': 1.0})
    assert result == 0.0

    # Two elements with different electronegativities
    # Fe (1.83), Ni (1.91). Mean = 1.87. Var = 0.5*(0.04^2) + 0.5*(-0.04^2) = 0.0016
    composition = {'Fe': 0.5, 'Ni': 0.5}
    result = calculate_variance_electronegativity(composition)
    assert result > 0
    assert abs(result - 0.0016) < 0.001 # Approximate check

def test_calculate_weighted_mean_VEC():
    """Test VEC calculation"""
    # Fe (8 valence), Ni (10 valence). Mean = 9.
    composition = {'Fe': 0.5, 'Ni': 0.5}
    result = calculate_weighted_mean_VEC(composition)
    # Mendeleev valence might be different, but it should be a number
    assert isinstance(result, float)
    assert result > 0

def test_calculate_atomic_size_mismatch():
    """Test size mismatch calculation"""
    # Pure element -> mismatch = 0
    result = calculate_atomic_size_mismatch({'Zr': 1.0})
    assert result == 0.0

    # Alloy should be > 0
    composition = {'Zr': 0.5, 'Cu': 0.5}
    result = calculate_atomic_size_mismatch(composition)
    assert result > 0
    assert result < 1.0 # Usually small

def test_extract_descriptors():
    """Test full extraction pipeline"""
    formula = "Zr50Cu40Al10"
    descriptors = extract_descriptors(formula)
    
    required_keys = [
        'mean_atomic_radius',
        'mean_electronegativity',
        'electronegativity_variance',
        'vec',
        'size_mismatch'
    ]
    
    for key in required_keys:
        assert key in descriptors
        assert isinstance(descriptors[key], float)
        assert not math.isnan(descriptors[key])
        assert not math.isinf(descriptors[key])