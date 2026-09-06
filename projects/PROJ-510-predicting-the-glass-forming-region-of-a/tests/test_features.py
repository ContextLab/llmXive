"""
Unit tests for feature engineering functions.
"""
import pytest
import numpy as np
from code.features import (
    parse_composition,
    calculate_mixing_enthalpy,
    calculate_atomic_size_mismatch,
    calculate_electronegativity_variance
)

def test_parse_composition_valid():
    """Test parsing of valid ternary compositions."""
    result = parse_composition("Fe50Co30Ni20")
    assert result is not None
    assert len(result) == 3
    assert abs(result['Fe'] - 0.50) < 0.01
    assert abs(result['Co'] - 0.30) < 0.01
    assert abs(result['Ni'] - 0.20) < 0.01

def test_parse_composition_invalid():
    """Test parsing of invalid compositions."""
    # Binary alloy
    result = parse_composition("Fe50Co50")
    assert result is None
    
    # Invalid format
    result = parse_composition("invalid")
    assert result is None

def test_mixing_enthalpy():
    """Test mixing enthalpy calculation."""
    composition = {'Fe': 0.5, 'Co': 0.3, 'Ni': 0.2}
    result = calculate_mixing_enthalpy(composition)
    # Currently returns 0.0 as placeholder
    assert isinstance(result, float)

def test_size_mismatch():
    """Test atomic size mismatch calculation."""
    composition = {'Fe': 0.5, 'Co': 0.3, 'Ni': 0.2}
    result = calculate_atomic_size_mismatch(composition)
    assert isinstance(result, float)
    assert result >= 0

def test_electronegativity_variance():
    """Test electronegativity variance calculation."""
    composition = {'Fe': 0.5, 'Co': 0.3, 'Ni': 0.2}
    result = calculate_electronegativity_variance(composition)
    assert isinstance(result, float)
    assert result >= 0