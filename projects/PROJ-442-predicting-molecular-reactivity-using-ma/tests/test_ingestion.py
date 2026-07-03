"""
Unit test for SMILES normalization and error logging.
"""
import pytest
from src.data.ingestion import normalize_smiles

def test_normalize_smiles_valid():
    # Placeholder for real normalization logic
    assert normalize_smiles("CCO") == "CCO"

def test_normalize_smiles_invalid():
    # Should handle empty or invalid
    assert normalize_smiles("") == ""
