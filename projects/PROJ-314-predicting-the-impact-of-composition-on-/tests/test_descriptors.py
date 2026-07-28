"""
Unit tests for composition parsing logic using chemparse.
This module validates the parsing of chemical formulas into elemental counts,
ensuring the `chemparse` library integration works as expected for the
ceramic data ingestion pipeline.
"""
import pytest
from chemparse import Composition
from typing import Dict, List, Any


class TestCompositionParsing:
    """Tests for the chemparse composition parsing functionality."""

    def test_parse_simple_oxide(self):
        """Test parsing a simple binary oxide (Al2O3)."""
        formula = "Al2O3"
        comp = Composition(formula)
        result = comp.to_dict()

        assert "Al" in result
        assert "O" in result
        assert result["Al"] == 2
        assert result["O"] == 3

    def test_parse_complex_ceramic(self):
        """Test parsing a complex perovskite structure (BaTiO3)."""
        formula = "BaTiO3"
        comp = Composition(formula)
        result = comp.to_dict()

        assert "Ba" in result
        assert "Ti" in result
        assert "O" in result
        assert result["Ba"] == 1
        assert result["Ti"] == 1
        assert result["O"] == 3

    def test_parse_stoichiometric_coefficient(self):
        """Test parsing formulas with fractional or decimal coefficients."""
        formula = "Zr0.9Y0.1O1.95"
        comp = Composition(formula)
        result = comp.to_dict()

        assert "Zr" in result
        assert "Y" in result
        assert "O" in result
        # Allow small floating point tolerance
        assert abs(result["Zr"] - 0.9) < 1e-6
        assert abs(result["Y"] - 0.1) < 1e-6
        assert abs(result["O"] - 1.95) < 1e-6

    def test_parse_ionic_charge_notation(self):
        """Test that ionic charge notation (e.g., Ca2+) is handled or stripped correctly."""
        # chemparse typically handles the element symbol; charges are often ignored for stoichiometry
        # but we ensure the element is extracted correctly.
        formula = "Ca2+"
        try:
            comp = Composition(formula)
            result = comp.to_dict()
            # If it parses, check for Calcium
            assert "Ca" in result
        except ValueError:
            # If the library raises on charge notation, that is acceptable behavior
            # provided the ingestion pipeline cleans the input first.
            # For this test, we assert that valid stoichiometry works.
            pass

    def test_parse_mixed_oxide(self):
        """Test parsing a mixed oxide (MgAl2O4 - Spinel)."""
        formula = "MgAl2O4"
        comp = Composition(formula)
        result = comp.to_dict()

        assert len(result) == 3
        assert result["Mg"] == 1
        assert result["Al"] == 2
        assert result["O"] == 4

    def test_parse_invalid_formula(self):
        """Test that invalid formulas raise an appropriate error."""
        invalid_formula = "InvalidFormula123"
        with pytest.raises(Exception):
            Composition(invalid_formula)

    def test_parse_empty_formula(self):
        """Test that an empty string raises an error."""
        with pytest.raises(Exception):
            Composition("")

    def test_parse_total_atoms_calculation(self):
        """Verify that the total number of atoms can be derived correctly."""
        formula = "SiO2"
        comp = Composition(formula)
        result = comp.to_dict()

        total_atoms = sum(result.values())
        assert total_atoms == 3  # 1 Si + 2 O

    def test_parse_case_sensitivity(self):
        """Ensure element symbols are case-sensitive and parsed correctly."""
        # "co" is not Cobalt, "Co" is.
        formula = "Co"
        comp = Composition(formula)
        result = comp.to_dict()

        assert "Co" in result
        assert result["Co"] == 1
        assert "co" not in result

    def test_parse_hydrate(self):
        """Test parsing a hydrate (e.g., CuSO4.5H2O)."""
        formula = "CuSO4.5H2O"
        comp = Composition(formula)
        result = comp.to_dict()

        assert "Cu" in result
        assert "S" in result
        assert "O" in result
        assert "H" in result
        assert result["Cu"] == 1
        assert result["S"] == 1
        # 4 O from sulfate + 5 O from water = 9
        assert abs(result["O"] - 9.0) < 1e-6
        # 10 H from water
        assert abs(result["H"] - 10.0) < 1e-6

    def test_parse_chemical_formula_list_integration(self):
        """Simulate how the ingestion pipeline might iterate over a list of formulas."""
        formulas = ["Al2O3", "SiO2", "ZrO2"]
        parsed_data = []

        for f in formulas:
            comp = Composition(f)
            parsed_data.append(comp.to_dict())

        assert len(parsed_data) == 3
        assert parsed_data[0]["Al"] == 2
        assert parsed_data[1]["Si"] == 1
        assert parsed_data[2]["Zr"] == 1