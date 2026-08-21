"""Unit tests for ingestion module (SMILES validation)."""
import pytest
from rdkit import Chem
from ingest import is_valid_smiles

def test_smiles_validation_rejects_invalid():
    """Test that invalid SMILES strings are rejected."""
    # Invalid SMILES examples
    # "C1CC1C1CC1" has conflicting ring closures
    assert not is_valid_smiles("C1CC1C1CC1")
    # "C#N@" contains an invalid atom symbol
    assert not is_valid_smiles("C#N@")
    # "CC(=O)O)" has an unmatched parenthesis
    assert not is_valid_smiles("CC(=O)O)")
    # Empty string
    assert not is_valid_smiles("")
    # None input
    assert not is_valid_smiles(None)
    
    # Edge case: A string that looks like SMILES but fails RDKit sanitization
    # e.g., a ring with impossible valence
    assert not is_valid_smiles("C1=CC=CC=C1C#C#C") # Cumulative triple bonds often fail valence check in some contexts, 
                                                   # but specifically testing strict rejection of known bad patterns
    # Explicitly invalid ring closure number usage
    assert not is_valid_smiles("C1CC2")

def test_smiles_validation_accepts_valid():
    """Test that valid SMILES strings are accepted."""
    # Valid SMILES examples
    assert is_valid_smiles("CCO")  # Ethanol
    assert is_valid_smiles("CC(=O)O")  # Acetic acid
    assert is_valid_smiles("C1=CC=CC=C1")  # Benzene
    assert is_valid_smiles("CC(=O)OC1=CC=CC=C1C(=O)O")  # Aspirin
    assert is_valid_smiles("C[C@H](O)[C@@H](C)O")  # Chiral valid

def test_validate_smiles_and_convert_rejects_invalid():
    """Test the full conversion pipeline rejects invalid SMILES."""
    from ingest import validate_smiles_and_convert
    
    assert validate_smiles_and_convert("C1CC1C1CC1") is None
    assert validate_smiles_and_convert("CC(=O)O)") is None
    assert validate_smiles_and_convert("") is None
    assert validate_smiles_and_convert(None) is None

def test_validate_smiles_and_convert_accepts_valid():
    """Test the full conversion pipeline accepts valid SMILES."""
    from ingest import validate_smiles_and_convert
    
    mol = validate_smiles_and_convert("CCO")
    assert mol is not None
    assert isinstance(mol, Chem.Mol)
    
    mol = validate_smiles_and_convert("C1=CC=CC=C1")
    assert mol is not None
    assert mol.GetNumAtoms() == 6