"""
Tests for utility functions.
"""
import pytest
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.utils import (
    get_element_property,
    get_element_properties,
    normalize_element_symbol,
    validate_composition
)

class TestElementProperties:
    def test_atomic_mass(self):
        mass = get_element_property('Fe', 'atomic_mass')
        assert mass is not None
        assert isinstance(mass, (int, float))
        assert mass > 0

    def test_electronegativity(self):
        chi = get_element_property('Cu', 'electronegativity')
        assert chi is not None
        assert isinstance(chi, (int, float))

    def test_invalid_element(self):
        with pytest.raises(ValueError):
            get_element_property('Xx', 'atomic_mass')

class TestNormalizeSymbol:
    def test_lowercase(self):
        assert normalize_element_symbol('cu') == 'Cu'
        assert normalize_element_symbol('FE') == 'Fe'

    def test_invalid(self):
        with pytest.raises(ValueError):
            normalize_element_symbol('x')

class TestValidateComposition:
    def test_valid(self):
        assert validate_composition('Cu50Zr50') is True
        assert validate_composition('Cu_50_Zr_50') is True

    def test_invalid(self):
        assert validate_composition('Xx50Yy50') is False
        assert validate_composition('Cu60Zr50') is False # Sum != 100
