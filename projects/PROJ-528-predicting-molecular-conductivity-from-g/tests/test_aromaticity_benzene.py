import pytest
from rdkit import Chem
from code.descriptors import compute_huckel_aromaticity_index

def test_aromaticity_index_benzene():
    """
    Test the Hückel aromaticity index calculation on benzene.
    
    Benzene (SMILES: "c1ccccc1") is the canonical aromatic system.
    According to Hückel's rule (4n+2 π electrons), it should have a
    non-zero aromaticity index. This test is expected to fail until
    the implementation in code/descriptors.py is complete.
    
    Expected behavior:
    - The function should return a positive float for benzene
    - The value should be consistent with aromatic systems (typically > 0)
    """
    smiles = "c1ccccc1"
    mol = Chem.MolFromSmiles(smiles)
    
    assert mol is not None, f"Failed to parse SMILES: {smiles}"
    
    # This will fail until compute_huckel_aromaticity_index is implemented
    result = compute_huckel_aromaticity_index(mol)
    
    # Benzene should have a positive aromaticity index
    assert result > 0, f"Benzene aromaticity index should be positive, got {result}"
    
    # Expected value for benzene is typically around 1.0 (normalized Hückel index)
    # This is a rough check - the exact value depends on implementation details
    assert 0.5 < result < 1.5, f"Benzene aromaticity index out of expected range: {result}"

def test_aromaticity_index_non_aromatic():
    """
    Test that non-aromatic molecules return zero or near-zero aromaticity index.
    """
    # Cyclohexane is not aromatic
    smiles = "C1CCCCC1"
    mol = Chem.MolFromSmiles(smiles)
    
    assert mol is not None, f"Failed to parse SMILES: {smiles}"
    
    result = compute_huckel_aromaticity_index(mol)
    
    # Non-aromatic systems should have zero or very low index
    assert result <= 0.1, f"Non-aromatic system should have near-zero index, got {result}"

def test_aromaticity_index_pyridine():
    """
    Test aromaticity index on pyridine (heteroaromatic).
    """
    smiles = "c1ccncc1"
    mol = Chem.MolFromSmiles(smiles)
    
    assert mol is not None, f"Failed to parse SMILES: {smiles}"
    
    result = compute_huckel_aromaticity_index(mol)
    
    # Pyridine is aromatic and should have a positive index
    assert result > 0, f"Pyridine aromaticity index should be positive, got {result}"