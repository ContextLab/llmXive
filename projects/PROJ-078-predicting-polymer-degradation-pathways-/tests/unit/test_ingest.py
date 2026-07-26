"""Unit tests for ingestion logic."""
import pytest
from rdkit import Chem
from ingest import is_valid_smiles, validate_degradation_label

class TestSMILESValidation:
    def test_is_valid_smiles_accepts_valid(self):
        """Test that valid SMILES are accepted."""
        assert is_valid_smiles("CC(=O)O") is True
        assert is_valid_smiles("C1CCCCC1") is True

    def test_is_valid_smiles_rejects_invalid(self):
        """Test that invalid SMILES are rejected."""
        assert is_valid_smiles("invalid_smiles_123") is False
        assert is_valid_smiles("") is False
        assert is_valid_smiles(None) is False

class TestLabelValidation:
    def test_validate_degradation_label_accepts_valid(self):
        """Test valid labels are accepted."""
        assert validate_degradation_label("hydrolysis") is True
        assert validate_degradation_label("oxidation") is True
        assert validate_degradation_label("photolysis") is True

    def test_validate_degradation_label_rejects_invalid(self):
        """Test invalid labels are rejected."""
        assert validate_degradation_label("unknown_type") is False
        assert validate_degradation_label("") is False
        assert validate_degradation_label(None) is False
