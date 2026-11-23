"""
Unit tests for ingestion logic.
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.ingest_utils import celsius_to_kelvin, pascal_to_gpa, validate_weight_fractions, is_valid_smiles

class TestUnitConversion:
    """Unit tests for unit conversion functions."""

    def test_celsius_to_kelvin(self):
        """Test Celsius to Kelvin conversion."""
        assert celsius_to_kelvin(0) == 273.15
        assert celsius_to_kelvin(25.0) == 298.15
        assert celsius_to_kelvin(-273.15) == 0.0

    def test_pascal_to_gpa(self):
        """Test Pascal to GPa conversion."""
        assert pascal_to_gpa(1e9) == 1.0
        assert pascal_to_gpa(2.5e9) == 2.5
        assert pascal_to_gpa(1e6) == 0.001

class TestWeightFractionValidation:
    """Unit tests for weight fraction validation."""

    def test_valid_weight_fractions(self):
        """Test validation of valid weight fractions."""
        # Sum exactly 1.0
        assert validate_weight_fractions([0.5, 0.5], tolerance=0.02) is True
        # Sum within tolerance
        assert validate_weight_fractions([0.49, 0.52], tolerance=0.02) is True

    def test_invalid_weight_fractions(self):
        """Test validation of invalid weight fractions."""
        # Sum exceeds tolerance
        assert validate_weight_fractions([0.4, 0.4], tolerance=0.02) is False
        # Sum far from 1.0
        assert validate_weight_fractions([0.8, 0.8], tolerance=0.02) is False

class TestSMILESValidation:
    """Unit tests for SMILES validation."""

    def test_valid_smiles(self):
        """Test validation of valid SMILES strings."""
        assert is_valid_smiles("CCO") is True  # Ethanol
        assert is_valid_smiles("c1ccccc1") is True  # Benzene

    def test_invalid_smiles(self):
        """Test validation of invalid SMILES strings."""
        assert is_valid_smiles("invalid_smiles") is False
        assert is_valid_smiles("") is False
