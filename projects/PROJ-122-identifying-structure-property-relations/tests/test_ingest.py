"""
Unit tests for ingestion logic: unit conversion, weight-fraction validation, SMILES parsing.
"""
import pytest
import math
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.ingest_utils import celsius_to_kelvin, pascal_to_gpa, validate_weight_fractions, is_valid_smiles

# --- Unit Conversion Tests ---
def test_celsius_to_kelvin():
    """Test conversion from Celsius to Kelvin."""
    celsius = 25.0
    kelvin = celsius_to_kelvin(celsius)
    assert math.isclose(kelvin, 298.15, rel_tol=1e-2)

    # Test absolute zero
    celsius = -273.15
    kelvin = celsius_to_kelvin(celsius)
    assert math.isclose(kelvin, 0.0, rel_tol=1e-2)

def test_pa_to_gpa():
    """Test conversion from Pascal to GPa."""
    pa = 1e9
    gpa = pascal_to_gpa(pa)
    assert math.isclose(gpa, 1.0, rel_tol=1e-2)

    # Test 100 MPa
    pa = 100e6
    gpa = pascal_to_gpa(pa)
    assert math.isclose(gpa, 0.1, rel_tol=1e-2)

# --- Weight Fraction Validation Tests ---
def test_weight_fraction_sum_valid():
    """Test that valid weight fractions sum to ~1.0 within tolerance (±0.02)."""
    fractions = [0.4, 0.6]
    is_valid, message = validate_weight_fractions(fractions, tolerance=0.02)
    assert is_valid
    assert "valid" in message.lower()

def test_weight_fraction_sum_invalid_high():
    """Test that weight fractions summing > 1.02 are flagged as invalid."""
    fractions = [0.5, 0.6] # Sum = 1.1
    is_valid, message = validate_weight_fractions(fractions, tolerance=0.02)
    assert not is_valid
    assert "invalid" in message.lower() or "exceeds" in message.lower()

def test_weight_fraction_sum_invalid_low():
    """Test that weight fractions summing < 0.98 are flagged as invalid."""
    fractions = [0.4, 0.4] # Sum = 0.8
    is_valid, message = validate_weight_fractions(fractions, tolerance=0.02)
    assert not is_valid
    assert "invalid" in message.lower() or "below" in message.lower()

def test_weight_fraction_sum_edge_case_upper():
    """Test edge case: sum = 1.02 (should be valid)."""
    fractions = [0.51, 0.51] # Sum = 1.02
    is_valid, message = validate_weight_fractions(fractions, tolerance=0.02)
    assert is_valid

def test_weight_fraction_sum_edge_case_lower():
    """Test edge case: sum = 0.98 (should be valid)."""
    fractions = [0.49, 0.49] # Sum = 0.98
    is_valid, message = validate_weight_fractions(fractions, tolerance=0.02)
    assert is_valid

# --- SMILES Parsing Tests ---
def test_smiles_parsing_valid():
    """Test parsing of a valid SMILES string."""
    smiles = "CCO"  # Ethanol
    result = is_valid_smiles(smiles)
    assert result is True

def test_smiles_parsing_invalid():
    """Test handling of invalid SMILES string."""
    smiles = "INVALID_SMILES_$$"
    result = is_valid_smiles(smiles)
    assert result is False

def test_smiles_parsing_empty():
    """Test handling of empty SMILES string."""
    smiles = ""
    result = is_valid_smiles(smiles)
    assert result is False

def test_smiles_parsing_none():
    """Test handling of None SMILES string."""
    result = is_valid_smiles(None)
    assert result is False

def test_smiles_parsing_complex():
    """Test parsing of a complex valid SMILES string."""
    smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin
    result = is_valid_smiles(smiles)
    assert result is True