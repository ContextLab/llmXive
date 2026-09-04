"""
Unit tests for feature engineering functions.
"""
import pytest
import numpy as np
from features import (
    parse_composition,
    calculate_atomic_size_mismatch,
    calculate_electronegativity_variance
)

def test_parse_composition_valid():
    """Test parsing a valid ternary composition."""
    comp = parse_composition("Fe40Ni40B20")
    assert comp is not None
    assert len(comp) == 3
    assert comp['Fe'] == 40.0
    assert comp['Ni'] == 40.0
    assert comp['B'] == 20.0

def test_parse_composition_invalid():
    """Test parsing an invalid composition."""
    # Not ternary
    comp = parse_composition("Fe50Ni50")
    assert comp is None
    
    # Invalid element
    comp = parse_composition("X99Y1Z0")
    assert comp is None

def test_atomic_size_mismatch():
    """Test atomic size mismatch calculation."""
    # Fe-Ni-B system
    comp = {
        'Fe': 0.4,
        'Ni': 0.4,
        'B': 0.2
    }
    
    delta = calculate_atomic_size_mismatch(comp)
    assert isinstance(delta, float)
    assert delta >= 0
    # Typical values for metallic glasses are around 2-10%
    assert 0 < delta < 20

def test_electronegativity_variance():
    """Test electronegativity variance calculation."""
    comp = {
        'Fe': 0.4,
        'Ni': 0.4,
        'B': 0.2
    }
    
    variance = calculate_electronegativity_variance(comp)
    assert isinstance(variance, float)
    assert variance >= 0

def test_mixing_enthalpy_error():
    """Test that mixing enthalpy raises ValueError due to missing data."""
    from features import calculate_mixing_enthalpy
    
    comp = {
        'Fe': 0.4,
        'Ni': 0.4,
        'B': 0.2
    }
    
    with pytest.raises(ValueError, match="Pairwise enthalpy of mixing data not available"):
        calculate_mixing_enthalpy(comp)
