"""
Unit tests for code/utils/parsers.py
"""
import pytest
from rdkit import Chem
import logging

# Import the module under test
# Assuming the project structure puts utils in code/utils
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.parsers import (
    smiles_to_mol, 
    parse_xyz_to_mol, 
    validate_molecule, 
    parse_smiles_list
)

# Setup logging to see warnings during tests if needed
logging.basicConfig(level=logging.WARNING)

class TestSmilesParsing:
    def test_valid_smiles(self):
        """Test parsing a valid SMILES string."""
        mol = smiles_to_mol("CCO") # Ethanol
        assert mol is not None
        assert mol.GetNumAtoms() == 3 # C-C-O
        assert mol.GetNumBonds() == 2

    def test_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        mol = smiles_to_mol("C(Invalid)")
        assert mol is None

    def test_empty_smiles(self):
        """Test handling of empty string."""
        mol = smiles_to_mol("")
        assert mol is None

    def test_none_smiles(self):
        """Test handling of None input."""
        mol = smiles_to_mol(None)
        assert mol is None

    def test_benzene(self):
        """Test parsing benzene."""
        mol = smiles_to_mol("c1ccccc1")
        assert mol is not None
        assert mol.GetNumAtoms() == 6

class TestXYZParsing:
    def test_valid_xyz_string(self):
        """Test parsing valid XYZ content from a string."""
        # Water molecule
        xyz_str = """3
        Water molecule
        O 0.000000 0.000000 0.000000
        H 0.757000 0.586000 0.000000
        H -0.757000 0.586000 0.000000
        """
        mol = parse_xyz_to_mol(xyz_str)
        assert mol is not None
        assert mol.GetNumAtoms() == 3

    def test_valid_xyz_list(self):
        """Test parsing valid XYZ content from a list of lines."""
        xyz_lines = [
            "2",
            "Hydrogen molecule",
            "H 0.0 0.0 0.0",
            "H 0.74 0.0 0.0"
        ]
        mol = parse_xyz_to_mol(xyz_lines)
        assert mol is not None
        assert mol.GetNumAtoms() == 2

    def test_invalid_atom_count(self):
        """Test handling of mismatched atom count in header."""
        xyz_str = """2
        Mismatch
        C 0.0 0.0 0.0
        """
        mol = parse_xyz_to_mol(xyz_str)
        assert mol is None

    def test_malformed_coordinates(self):
        """Test handling of non-numeric coordinates."""
        xyz_str = """1
        Bad Coords
        C 0.0 abc 0.0
        """
        mol = parse_xyz_to_mol(xyz_str)
        assert mol is None

    def test_empty_xyz(self):
        """Test handling of empty input."""
        assert parse_xyz_to_mol("") is None
        assert parse_xyz_to_mol([]) is None

class TestValidation:
    def test_valid_molecule_2d(self):
        """Test validation of a 2D molecule."""
        mol = smiles_to_mol("CCO")
        is_valid, reason = validate_molecule(mol)
        assert is_valid
        assert "2D" in reason

    def test_valid_molecule_3d(self):
        """Test validation of a 3D molecule."""
        xyz_str = """1
        Atom
        C 0.0 0.0 0.0
        """
        mol = parse_xyz_to_mol(xyz_str)
        # RDKit MolFromXYZBlock creates a molecule with a conformer
        is_valid, reason = validate_molecule(mol)
        assert is_valid
        assert "Valid molecule" in reason

    def test_none_molecule(self):
        """Test validation of None."""
        is_valid, reason = validate_molecule(None)
        assert not is_valid
        assert "None" in reason

    def test_empty_molecule(self):
        """Test validation of an empty molecule object."""
        mol = Chem.Mol()
        is_valid, reason = validate_molecule(mol)
        assert not is_valid
        assert "no atoms" in reason

class TestParseSmilesList:
    def test_mixed_list(self):
        """Test parsing a list with valid and invalid SMILES."""
        input_list = ["CCO", "INVALID", "c1ccccc1", ""]
        mols = parse_smiles_list(input_list)
        # Should return 2 valid molecules (Ethanol, Benzene)
        assert len(mols) == 2
        assert mols[0].GetNumAtoms() == 3
        assert mols[1].GetNumAtoms() == 6

    def test_empty_list(self):
        """Test parsing an empty list."""
        mols = parse_smiles_list([])
        assert len(mols) == 0