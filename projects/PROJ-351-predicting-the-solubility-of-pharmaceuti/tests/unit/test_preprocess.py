"""
Unit tests for SMILES validation logic in code/data/preprocess.py.

Tests verify that:
1. Valid SMILES strings are processed correctly.
2. Invalid or malformed SMILES strings are rejected.
3. Empty or whitespace-only strings are rejected.
"""
import pytest
from rdkit import Chem
from data.preprocess import process_molecule, get_atom_features, get_bond_features


class TestSMILESValidation:
    """Tests for SMILES string validation and molecule processing."""

    def test_valid_smiles_caffeine(self):
        """Test processing of a valid SMILES string (Caffeine)."""
        smiles = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
        mol, atom_feats, bond_feats = process_molecule(smiles)
        
        assert mol is not None, "Molecule object should not be None for valid SMILES"
        assert isinstance(mol, Chem.Mol)
        assert mol.GetNumAtoms() > 0
        assert atom_feats is not None
        assert len(atom_feats) == mol.GetNumAtoms()
        assert bond_feats is not None
        assert len(bond_feats) == mol.GetNumBonds()

    def test_valid_smiles_benzene(self):
        """Test processing of a valid SMILES string (Benzene)."""
        smiles = "c1ccccc1"
        mol, atom_feats, bond_feats = process_molecule(smiles)
        
        assert mol is not None
        assert mol.GetNumAtoms() == 6
        assert mol.GetNumBonds() == 6

    def test_invalid_smiles_random_characters(self):
        """Test that random characters are rejected as invalid SMILES."""
        smiles = "xyz123!@#"
        mol, atom_feats, bond_feats = process_molecule(smiles)
        
        assert mol is None, "Molecule should be None for invalid SMILES"
        assert atom_feats is None
        assert bond_feats is None

    def test_invalid_smiles_mismatched_parens(self):
        """Test that mismatched parentheses result in rejection."""
        smiles = "CC(C)C(=O)O"  # Valid
        smiles_invalid = "CC(C)C(=O"  # Invalid: mismatched parenthesis
        
        mol_valid, _, _ = process_molecule(smiles)
        mol_invalid, _, _ = process_molecule(smiles_invalid)
        
        assert mol_valid is not None
        assert mol_invalid is None

    def test_invalid_smiles_empty_string(self):
        """Test that empty string is rejected."""
        smiles = ""
        mol, atom_feats, bond_feats = process_molecule(smiles)
        
        assert mol is None
        assert atom_feats is None
        assert bond_feats is None

    def test_invalid_smiles_whitespace_only(self):
        """Test that whitespace-only string is rejected."""
        smiles = "   "
        mol, atom_feats, bond_feats = process_molecule(smiles)
        
        assert mol is None
        assert atom_feats is None
        assert bond_feats is None

    def test_invalid_smiles_null_terminator(self):
        """Test that string with null terminator is rejected."""
        smiles = "CCO\x00"
        mol, atom_feats, bond_feats = process_molecule(smiles)
        
        assert mol is None

    def test_valid_smiles_with_stereochemistry(self):
        """Test processing of SMILES with stereochemistry markers."""
        smiles = "C/C=C/C"  # trans-2-butene
        mol, atom_feats, bond_feats = process_molecule(smiles)
        
        assert mol is not None
        assert mol.GetNumAtoms() == 4

    def test_invalid_smiles_unrecognized_atom(self):
        """Test that unrecognized atoms (e.g., 'X') are rejected."""
        # 'X' is not a valid element symbol in RDKit without explicit bracket notation
        smiles = "CXX"
        mol, atom_feats, bond_feats = process_molecule(smiles)
        
        # RDKit might interpret 'X' as an atom if it's in brackets, but "CXX" is likely invalid
        # Let's test with a clearly invalid element
        smiles_invalid = "CQZ"  # Q and Z are not standard elements
        mol_invalid, _, _ = process_molecule(smiles_invalid)
        assert mol_invalid is None

    def test_atom_features_shape(self):
        """Test that atom features are returned with correct shape for valid molecule."""
        smiles = "CCO"
        mol, atom_feats, _ = process_molecule(smiles)
        
        assert mol is not None
        assert len(atom_feats) == mol.GetNumAtoms()
        # Each atom should have a feature vector (list or numpy array)
        for feat in atom_feats:
            assert len(feat) > 0

    def test_bond_features_shape(self):
        """Test that bond features are returned with correct shape for valid molecule."""
        smiles = "CCO"
        mol, _, bond_feats = process_molecule(smiles)
        
        assert mol is not None
        assert len(bond_feats) == mol.GetNumBonds()
        for feat in bond_feats:
            assert len(feat) > 0

    def test_edge_case_single_atom(self):
        """Test processing of a single atom SMILES."""
        smiles = "C"
        mol, atom_feats, bond_feats = process_molecule(smiles)
        
        assert mol is not None
        assert mol.GetNumAtoms() == 1
        assert mol.GetNumBonds() == 0
        assert len(atom_feats) == 1
        assert len(bond_feats) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])