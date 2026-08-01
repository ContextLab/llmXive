"""
Unit tests for salt removal and SMILES standardization.
"""

import pytest
import pandas as pd
from preprocessing.sanitize import remove_salts, standardize_smiles, parse_yield

class TestRemoveSalts:
    def test_remove_single_salt(self):
        """Test removal of a single salt fragment."""
        smiles = "CCO.[Na]"  # Ethanol + Sodium
        result = remove_salts([smiles])
        assert len(result) == 1
        assert result[0] == "CCO"  # Should keep ethanol

    def test_remove_multiple_salts(self):
        """Test removal of multiple salt fragments."""
        smiles = "CCO.[Na].[Cl]"  # Ethanol + Sodium + Chlorine
        result = remove_salts([smiles])
        assert len(result) == 1
        assert result[0] == "CCO"

    def test_no_salts(self):
        """Test molecule without salts remains unchanged."""
        smiles = "CCO"
        result = remove_salts([smiles])
        assert result[0] == smiles

    def test_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        smiles = "invalid_smiles"
        result = remove_salts([smiles])
        assert result[0] == smiles  # Should return original

    def test_empty_list(self):
        """Test empty input list."""
        result = remove_salts([])
        assert result == []

class TestStandardizeSmiles:
    def test_standardize_valid_smiles(self):
        """Test standardization of valid SMILES."""
        smiles = "CCO"
        result = standardize_smiles(smiles)
        assert result is not None
        assert result == "CCO"  # Canonical form

    def test_standardize_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        smiles = "invalid"
        result = standardize_smiles(smiles)
        assert result is None

    def test_standardize_empty_string(self):
        """Test handling of empty string."""
        result = standardize_smiles("")
        assert result is None

    def test_standardize_none(self):
        """Test handling of None."""
        result = standardize_smiles(None)
        assert result is None

class TestParseYield:
    def test_parse_single_value(self):
        """Test parsing of single yield value."""
        assert parse_yield(80) == 80.0
        assert parse_yield(80.5) == 80.5
        assert parse_yield("80") == 80.0

    def test_parse_percentage(self):
        """Test parsing of percentage string."""
        assert parse_yield("80%") == 80.0
        assert parse_yield("85.5%") == 85.5

    def test_parse_range(self):
        """Test parsing of yield range."""
        assert parse_yield("80-90") == 85.0
        assert parse_yield("70.5-80.5") == 75.5

    def test_parse_invalid(self):
        """Test handling of invalid yield."""
        assert parse_yield("invalid") is None
        assert parse_yield("80-") is None
        assert parse_yield("-90") is None

    def test_parse_null(self):
        """Test handling of null yield."""
        import pandas as pd
        assert pd.isna(parse_yield(None))
        assert pd.isna(parse_yield(float('nan')))
