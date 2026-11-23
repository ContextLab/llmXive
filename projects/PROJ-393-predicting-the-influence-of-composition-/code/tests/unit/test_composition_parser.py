"""
Unit Tests for Composition Parser.

Tests the conversion of chemical formula strings to atomic fractions.
"""
import pytest
import sys
from pathlib import Path
from typing import Dict

# Ensure the src directory is in the path for imports
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from preprocessing.composition_parser import parse_composition, parse_formula_to_fractions


class TestCompositionParser:
    """Test suite for composition parsing logic."""

    def test_standard_heusler_formula(self):
        """Test parsing of a standard Heusler formula: Co2MnGa."""
        result = parse_composition("Co2MnGa")
        
        assert "Co" in result
        assert "Mn" in result
        assert "Ga" in result
        
        # Total atoms: 2 (Co) + 1 (Mn) + 1 (Ga) = 4
        # Fractions: Co=0.5, Mn=0.25, Ga=0.25
        assert abs(result["Co"] - 0.5) < 1e-4
        assert abs(result["Mn"] - 0.25) < 1e-4
        assert abs(result["Ga"] - 0.25) < 1e-4
        
        # Sum should be 1.0
        assert abs(sum(result.values()) - 1.0) < 1e-4

    def test_simple_binary_alloy(self):
        """Test parsing of a simple binary alloy: FeNi3."""
        result = parse_composition("FeNi3")
        
        assert "Fe" in result
        assert "Ni" in result
        
        # Total atoms: 1 (Fe) + 3 (Ni) = 4
        assert abs(result["Fe"] - 0.25) < 1e-4
        assert abs(result["Ni"] - 0.75) < 1e-4
        assert abs(sum(result.values()) - 1.0) < 1e-4

    def test_element_without_count(self):
        """Test parsing where elements have implicit count of 1: MnFeCo."""
        result = parse_composition("MnFeCo")
        
        assert result["Mn"] == 0.3333
        assert result["Fe"] == 0.3333
        assert result["Co"] == 0.3333
        # Note: 1/3 is 0.333333..., rounded to 4 decimals is 0.3333
        # Sum might be 0.9999 due to rounding, which is acceptable per spec (>= 4 decimal places)
        # But let's check the specific rounding behavior
        assert abs(result["Mn"] - 0.3333) < 1e-5

    def test_empty_string_raises_error(self):
        """Test that an empty string raises a ValueError."""
        with pytest.raises(ValueError):
            parse_composition("")

    def test_whitespace_handling(self):
        """Test that leading/trailing whitespace is handled."""
        result = parse_composition("  Co2MnGa  ")
        assert result["Co"] == 0.5
        assert len(result) == 3

    def test_invalid_characters_raises_error(self):
        """Test that invalid characters (non-element) raise an error or are handled."""
        # The regex [A-Z][a-z]? should fail to match '1' or special chars at start
        # If the string is just numbers, it returns no matches
        with pytest.raises(ValueError):
            parse_composition("12345")

    def test_case_sensitivity(self):
        """Test that element symbols are case-sensitive (lowercase at start is invalid)."""
        # 'co2MnGa' -> 'co' is not a valid element match for standard regex [A-Z][a-z]?
        # The regex expects Capital first. 'co' would not match 'Co'.
        # However, the regex will match 'o' if it's after a capital? No.
        # Let's test 'Co' vs 'co'.
        with pytest.raises(ValueError):
            parse_composition("co2MnGa") 
            # 'co' -> 'c' (no match for [A-Z]), 'o' (no match). Actually, regex might match nothing or partial.
            # If regex matches nothing, it raises ValueError.

    def test_large_coefficient(self):
        """Test parsing with large coefficients."""
        result = parse_composition("Fe10Ni10")
        # Total 20. Fe=0.5, Ni=0.5
        assert abs(result["Fe"] - 0.5) < 1e-4
        assert abs(result["Ni"] - 0.5) < 1e-4

    def test_parse_formula_to_fractions_alias(self):
        """Test that the alias function works identically."""
        result1 = parse_composition("Co2MnGa")
        result2 = parse_formula_to_fractions("Co2MnGa")
        assert result1 == result2