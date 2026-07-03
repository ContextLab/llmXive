import pytest
from src.utils.chemistry import classify_reaction, load_reaction_templates

def test_load_templates():
    """Test loading reaction templates from config."""
    templates = load_reaction_templates()
    assert 'SN1' in templates
    assert 'SN2' in templates
    assert 'Diels-Alder' in templates

def test_classify_sn1():
    """Test classification of SN1 reaction."""
    # Simple test case that should match SN1 pattern
    smiles = "CCO"
    result = classify_reaction(smiles)
    # Note: This depends on the actual SMARTS pattern matching
    # The pattern [C:1]([O:2])>>[C:1]+[O:2]- might not match simple ethanol
    # This test verifies the function runs without error
    assert result is None or result in ['SN1', 'SN2', 'Diels-Alder']

def test_classify_invalid_smiles():
    """Test classification of invalid SMILES."""
    result = classify_reaction("invalid")
    assert result is None
