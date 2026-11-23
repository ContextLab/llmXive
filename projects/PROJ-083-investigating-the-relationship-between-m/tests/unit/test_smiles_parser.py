"""
Unit tests for the SMILES parser utility.
"""

import pytest
from rdkit import Chem

from code.utils.smiles_parser import SMILESParser, BaseDataLoader, parse_smiles, load_smiles_file


class TestSMILESParser:
    """Tests for the SMILESParser class."""

    def test_parse_valid_benzene(self):
        """Test parsing a valid benzene SMILES."""
        parser = SMILESParser()
        mol = parser.parse("c1ccccc1")
        assert mol is not None
        assert mol.GetNumAtoms() == 6

    def test_parse_invalid_smiles(self):
        """Test parsing an invalid SMILES string."""
        parser = SMILESParser()
        mol = parser.parse("invalid_smiles_123")
        assert mol is None

    def test_parse_empty_string(self):
        """Test parsing an empty string."""
        parser = SMILESParser()
        mol = parser.parse("")
        assert mol is None

    def test_parse_none_input(self):
        """Test parsing None input."""
        parser = SMILESParser()
        mol = parser.parse(None)
        assert mol is None

    def test_get_molecular_formula(self):
        """Test molecular formula calculation."""
        parser = SMILESParser()
        mol = parser.parse("c1ccccc1")  # Benzene
        formula = parser.get_molecular_formula(mol)
        assert formula == "C6H6"

    def test_get_molecular_weight(self):
        """Test molecular weight calculation."""
        parser = SMILESParser()
        mol = parser.parse("c1ccccc1")  # Benzene
        weight = parser.get_molecular_weight(mol)
        # Benzene MW is approximately 78.11
        assert 78.0 < weight < 78.2

    def test_is_valid_aromatic_ring(self):
        """Test aromatic ring detection."""
        parser = SMILESParser()

        # Benzene should have aromatic ring
        mol = parser.parse("c1ccccc1")
        assert parser.is_valid_aromatic_ring(mol) is True

        # Hexane should not have aromatic ring
        mol = parser.parse("CCCCCC")
        assert parser.is_valid_aromatic_ring(mol) is False

    def test_parse_batch(self):
        """Test batch parsing."""
        parser = SMILESParser()
        smiles_list = ["c1ccccc1", "invalid", "CCO"]
        results = parser.parse_batch(smiles_list)

        assert len(results) == 3
        assert results[0][1] is not None  # Benzene
        assert results[1][1] is None      # Invalid
        assert results[2][1] is not None  # Ethanol


class TestBaseDataLoader:
    """Tests for the BaseDataLoader class."""

    def test_filter_valid(self, tmp_path):
        """Test filtering valid molecules."""
        # Create a temporary CSV file
        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text("smiles\n"
                            "c1ccccc1\n"
                            "invalid\n"
                            "CCO\n")

        loader = BaseDataLoader()
        records = loader.load_from_file(str(csv_file))
        valid_records = loader.filter_valid(records)

        assert len(valid_records) == 2
        assert all(r["valid"] for r in valid_records)

    def test_get_statistics(self, tmp_path):
        """Test statistics calculation."""
        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text("smiles\n"
                            "c1ccccc1\n"
                            "invalid\n"
                            "CCO\n"
                            "c1ccccc1\n")

        loader = BaseDataLoader()
        records = loader.load_from_file(str(csv_file))
        stats = loader.get_statistics(records)

        assert stats["total_records"] == 4
        assert stats["valid_molecules"] == 3
        assert stats["invalid_molecules"] == 1
        assert stats["molecules_with_aromatic_rings"] == 2


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_parse_smiles(self):
        """Test parse_smiles convenience function."""
        mol = parse_smiles("c1ccccc1")
        assert mol is not None
        assert mol.GetNumAtoms() == 6

    def test_load_smiles_file(self, tmp_path):
        """Test load_smiles_file convenience function."""
        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text("smiles\n"
                            "c1ccccc1\n"
                            "CCO\n")

        records = load_smiles_file(str(csv_file))
        assert len(records) == 2
        assert all(r["valid"] for r in records)
