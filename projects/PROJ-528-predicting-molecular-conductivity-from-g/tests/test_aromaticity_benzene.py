import pytest
from rdkit import Chem
from descriptors import compute_huckel_aromaticity_index

def test_aromaticity_index_benzene():
    """
    Test aromaticity index calculation on benzene (SMILES: "c1ccccc1").
    
    This test is expected to FAIL until the implementation of 
    compute_huckel_aromaticity_index is completed.
    
    Expected behavior:
    - Benzene is a classic aromatic system
    - The Hückel aromaticity index should be > 0 (indicating aromaticity)
    - Typically close to 1.0 for perfect aromatic systems
    """
    smiles = "c1ccccc1"
    mol = Chem.MolFromSmiles(smiles)
    
    assert mol is not None, f"Failed to parse SMILES: {smiles}"
    
    # This function is expected to exist in descriptors.py
    # but is not yet implemented, so this call will fail
    aromaticity_index = compute_huckel_aromaticity_index(mol)
    
    # Benzene should have a positive aromaticity index
    assert aromaticity_index > 0, f"Benzene should have positive aromaticity index, got {aromaticity_index}"
    
    # Should be close to 1.0 for a perfect aromatic system
    assert 0.8 <= aromaticity_index <= 1.2, \
        f"Benzene aromaticity index should be near 1.0, got {aromaticity_index}"

def test_aromaticity_index_non_aromatic():
    """
    Test that non-aromatic molecules return low or negative aromaticity index.
    
    Using cyclohexane (C1CCCCC1) as a non-aromatic reference.
    """
    smiles = "C1CCCCC1"  # cyclohexane
    mol = Chem.MolFromSmiles(smiles)
    
    assert mol is not None, f"Failed to parse SMILES: {smiles}"
    
    # This will fail until implementation is complete
    aromaticity_index = compute_huckel_aromaticity_index(mol)
    
    # Non-aromatic systems should have low or negative index
    assert aromaticity_index < 0.5, \
        f"Cyclohexane should have low aromaticity index, got {aromaticity_index}"

def test_aromaticity_index_pyridine():
    """
    Test aromaticity index on pyridine (heteroaromatic system).
    
    Pyridine (c1ccncc1) is aromatic but contains a nitrogen atom.
    """
    smiles = "c1ccncc1"  # pyridine
    mol = Chem.MolFromSmiles(smiles)
    
    assert mol is not None, f"Failed to parse SMILES: {smiles}"
    
    # This will fail until implementation is complete
    aromaticity_index = compute_huckel_aromaticity_index(mol)
    
    # Pyridine is aromatic, so index should be positive
    assert aromaticity_index > 0, f"Pyridine should have positive aromaticity index, got {aromaticity_index}"