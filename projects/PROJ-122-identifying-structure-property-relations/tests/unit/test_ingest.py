"""
Unit tests for data ingestion logic (US1).
"""
import pytest
from utils.ingest_utils import celsius_to_kelvin, pascal_to_gpa, validate_weight_fractions, is_valid_smiles

def test_celsius_to_kelvin():
    assert celsius_to_kelvin(0) == 273.15
    assert celsius_to_kelvin(25) == 298.15
    assert celsius_to_kelvin(-273.15) == 0.0

def test_pascal_to_gpa():
    assert pascal_to_gpa(1e9) == 1.0
    assert pascal_to_gpa(1e12) == 1000.0

def test_validate_weight_fractions():
    # Valid sum
    assert validate_weight_fractions([0.5, 0.5]) == (True, 1.0)
    # Valid with tolerance
    assert validate_weight_fractions([0.49, 0.49], tolerance=0.02) == (True, 0.98)
    # Invalid sum
    assert validate_weight_fractions([0.3, 0.3]) == (False, 0.6)

def test_is_valid_smiles():
    assert is_valid_smiles("CCO") == True
    assert is_valid_smiles("invalid_smiles_string") == False
