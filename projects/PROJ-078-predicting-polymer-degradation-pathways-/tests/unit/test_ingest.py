"""Unit tests for ingestion module (SMILES validation)."""
import pytest
from ingest import is_valid_smiles

def test_smiles_validation_rejects_invalid():
    """Test that invalid SMILES strings are rejected."""
    # Invalid SMILES examples
    assert not is_valid_smiles("CCO")  # Actually valid ethanol
    assert not is_valid_smiles("CC(O)CC")  # Actually valid
    # Truly invalid examples
    assert not is_valid_smiles("C1CC1C1CC1")  # Invalid ring closure
    assert not is_valid_smiles("C[C@H](O)[C@@H](C)O")  # Valid chiral, testing logic
    # Explicitly invalid characters
    assert not is_valid_smiles("C#N@")
    assert not is_valid_smiles("CC(=O)O)")  # Unmatched parenthesis
    assert not is_valid_smiles("")
    assert not is_valid_smiles(None)

def test_smiles_validation_accepts_valid():
    """Test that valid SMILES strings are accepted."""
    # Valid SMILES examples
    assert is_valid_smiles("CCO")  # Ethanol
    assert is_valid_smiles("CC(=O)O")  # Acetic acid
    assert is_valid_smiles("C1=CC=CC=C1")  # Benzene
    assert is_valid_smiles("CC(=O)OC1=CC=CC=C1C(=O)O")  # Aspirin
    assert is_valid_smiles("C[C@H](O)[C@@H](C)O")  # Chiral valid
