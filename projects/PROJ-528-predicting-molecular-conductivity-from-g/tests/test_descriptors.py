"""
Unit tests for descriptor computation functions.
"""
import pytest
import numpy as np
import pandas as pd
from rdkit import Chem
from code.descriptors import (
    compute_aromaticity_index,
    compute_conjugation_length,
    compute_num_conjugated_bonds,
    compute_all_descriptors,
    compute_aromatic_ring_count,
    compute_conjugated_ring_count
)

def test_aromaticity_benzene():
    """Test aromaticity index calculation on benzene."""
    smiles = "c1ccccc1"
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None, "Failed to parse benzene SMILES"
    
    aromaticity_index = compute_aromaticity_index(mol)
    assert aromaticity_index == 1.0, f"Expected aromaticity_index=1.0 for benzene, got {aromaticity_index}"

def test_conjugation_path_length():
    """Test conjugation path length on butadiene vs. butane."""
    butadiene_smiles = "C=CC=C"
    butane_smiles = "CCCC"
    
    butadiene_mol = Chem.MolFromSmiles(butadiene_smiles)
    butane_mol = Chem.MolFromSmiles(butane_smiles)
    
    assert butadiene_mol is not None, "Failed to parse butadiene SMILES"
    assert butane_mol is not None, "Failed to parse butane SMILES"
    
    butadiene_conj = compute_conjugation_length(butadiene_mol)
    butane_conj = compute_conjugation_length(butane_mol)
    
    assert butadiene_conj > butane_conj, f"Butadiene conjugation length ({butadiene_conj}) should be greater than butane ({butane_conj})"

def test_mixed_hybridization_descriptors():
    """Test descriptor computation on mixed hybridization molecules."""
    smiles = "CC=C"  # Propene: sp3 and sp2 carbons
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None, "Failed to parse mixed hybridization SMILES"
    
    # Compute all descriptors
    df = compute_all_descriptors(pd.DataFrame({'smiles': [smiles]}))
    
    # Check that all descriptor columns are finite numbers
    descriptor_cols = [col for col in df.columns if col not in ['smiles', 'status', 'error_msg']]
    for col in descriptor_cols:
        value = df[col].iloc[0]
        assert not np.isnan(value), f"NaN value found in {col}"
        assert np.isfinite(value), f"Infinite value found in {col}"

def test_aromatic_ring_count_benzene():
    """Test aromatic ring count on benzene."""
    smiles = "c1ccccc1"
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None
    
    count = compute_aromatic_ring_count(mol)
    assert count == 1, f"Expected 1 aromatic ring for benzene, got {count}"

def test_conjugated_ring_count_benzene():
    """Test conjugated ring count on benzene."""
    smiles = "c1ccccc1"
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None
    
    count = compute_conjugated_ring_count(mol)
    assert count == 1, f"Expected 1 conjugated ring for benzene, got {count}"

def test_conjugated_ring_count_cyclohexane():
    """Test conjugated ring count on cyclohexane (should be 0)."""
    smiles = "C1CCCCC1"
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None
    
    count = compute_conjugated_ring_count(mol)
    assert count == 0, f"Expected 0 conjugated rings for cyclohexane, got {count}"