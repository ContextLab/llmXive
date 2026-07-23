"""
Integration tests for SMILES validation and conversion pipeline.
"""
import pytest
from rdkit import Chem
from ingest import is_valid_smiles, validate_smiles_and_convert

class TestSMILESValidation:
    def test_valid_smiles(self, sample_smiles):
        """Test that a valid SMILES string is accepted."""
        assert is_valid_smiles(sample_smiles) is True

    def test_invalid_smiles(self, invalid_smiles):
        """Test that an invalid SMILES string is rejected."""
        assert is_valid_smiles(invalid_smiles) is False

    def test_convert_valid_smiles(self, sample_smiles):
        """Test conversion of valid SMILES to RDKit Mol object."""
        mol = validate_smiles_and_convert(sample_smiles)
        assert mol is not None
        assert isinstance(mol, Chem.Mol)
        assert Chem.MolToSmiles(mol) == Chem.MolToSmiles(Chem.MolFromSmiles(sample_smiles))

    def test_convert_invalid_smiles_raises(self, invalid_smiles):
        """Test that converting invalid SMILES raises an error."""
        with pytest.raises(ValueError):
            validate_smiles_and_convert(invalid_smiles)
