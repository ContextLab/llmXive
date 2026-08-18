"""
Unit tests for SMILES validation logic in code/data/loader.py.
Tests regex patterns and edge cases for input validation.
"""
import pytest
from code.data.loader import validate_smiles
from rdkit import Chem


class TestSmilesValidation:
    """Tests for the validate_smiles function."""

    def test_valid_simple_molecule(self):
        """Test validation of a simple valid SMILES string (ethane)."""
        smiles = "CC"
        assert validate_smiles(smiles) is True

    def test_valid_complex_molecule(self):
        """Test validation of a complex valid SMILES string (aspirin)."""
        smiles = "CC(=O)Oc1ccccc1C(=O)O"
        assert validate_smiles(smiles) is True

    def test_valid_with_rings(self):
        """Test validation of SMILES with ring closures."""
        smiles = "C1CCCCC1"
        assert validate_smiles(smiles) is True

    def test_valid_with_branches(self):
        """Test validation of SMILES with branches."""
        smiles = "CC(C)O"
        assert validate_smiles(smiles) is True

    def test_valid_with_charges(self):
        """Test validation of SMILES with ionic charges."""
        smiles = "[Na+].[Cl-]"
        assert validate_smiles(smiles) is True

    def test_invalid_empty_string(self):
        """Test rejection of empty string."""
        assert validate_smiles("") is False

    def test_invalid_none(self):
        """Test rejection of None input."""
        assert validate_smiles(None) is False

    def test_invalid_whitespace_only(self):
        """Test rejection of whitespace-only string."""
        assert validate_smiles("   ") is False

    def test_invalid_random_characters(self):
        """Test rejection of random non-SMILES characters."""
        smiles = "xyz!@#$%"
        assert validate_smiles(smiles) is False

    def test_invalid_unclosed_parenthesis(self):
        """Test rejection of SMILES with unclosed parenthesis."""
        smiles = "CC(O"
        assert validate_smiles(smiles) is False

    def test_invalid_unclosed_ring(self):
        """Test rejection of SMILES with mismatched ring numbers."""
        smiles = "C1CC2CCC1"
        assert validate_smiles(smiles) is False

    def test_invalid_bad_atom_symbol(self):
        """Test rejection of invalid atom symbols."""
        smiles = "CQ"  # Q is not a standard atom symbol in RDKit
        # RDKit might parse this as a query or fail; validate_smiles checks RDKit validity
        # If RDKit parses it but it's chemically nonsensical, we rely on RDKit's MolFromSmiles returning None or a warning
        # However, strictly invalid syntax should return False.
        # Let's test a clearly invalid syntax.
        smiles = "C@X"  # Invalid stereochemistry syntax or atom
        assert validate_smiles(smiles) is False

    def test_case_sensitivity(self):
        """Test that lowercase letters (aromatic) are handled correctly."""
        smiles = "c1ccccc1"  # Benzene in lowercase
        assert validate_smiles(smiles) is True

    def test_rdkit_mol_object_creation(self):
        """Verify that valid SMILES produce a valid RDKit Mol object."""
        smiles = "CCO"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None
        assert validate_smiles(smiles) is True

    def test_rdkit_fails_on_invalid(self):
        """Verify that invalid SMILES fail RDKit MolFromSmiles."""
        smiles = "invalid_smiles_string"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is None
        assert validate_smiles(smiles) is False
