"""
Unit tests for code/utils/constants.py
"""

import pytest
from code.utils.constants import get_metallic_radius, get_electronegativity, PERIODIC_TABLE_DATA

def test_get_metallic_radius_exists():
    """Test that metallic radius is returned for known elements."""
    radius = get_metallic_radius("Cu")
    assert radius is not None
    assert radius == 1.28

def test_get_metallic_radius_not_found():
    """Test that None is returned for unknown elements."""
    radius = get_metallic_radius("X")
    assert radius is None

def test_get_electronegativity_exists():
    """Test that electronegativity is returned for known elements."""
    en = get_electronegativity("Cu")
    assert en is not None
    assert en == 1.90

def test_get_electronegativity_not_found():
    """Test that None is returned for unknown elements."""
    en = get_electronegativity("X")
    assert en is None

def test_case_insensitivity():
    """Test that element symbols are case-insensitive."""
    radius_lower = get_metallic_radius("cu")
    radius_upper = get_metallic_radius("Cu")
    assert radius_lower == radius_upper

def test_periodic_table_data_structure():
    """Test that PERIODIC_TABLE_DATA has the expected structure."""
    for symbol, data in PERIODIC_TABLE_DATA.items():
        assert hasattr(data, 'metallic_radius')
        assert hasattr(data, 'electronegativity')
        assert hasattr(data, 'atomic_number')
        assert hasattr(data, 'symbol')
        assert data.symbol == symbol
