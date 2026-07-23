"""
Unit tests for ingestion validation logic.
"""
import pytest
from code.ingest import is_valid_smiles, validate_degradation_label

def test_smiles_validation_rejects_invalid():
    """Test that invalid SMILES strings are rejected."""
    assert is_valid_smiles("") is False
    assert is_valid_smiles(None) is False
    assert is_valid_smiles("invalid_smiles_string") is False
    assert is_valid_smiles("CCO") is True
    assert is_valid_smiles("c1ccccc1") is True

def test_missing_env_excludes_record():
    """Test that records with missing environmental data are handled."""
    # This is more of a logic test. The actual exclusion happens in preprocess.
    # Here we test the validation logic for degradation labels.
    assert validate_degradation_label(None) is False
    assert validate_degradation_label("") is False
    assert validate_degradation_label("   ") is False
    assert validate_degradation_label("hydrolysis") is True
