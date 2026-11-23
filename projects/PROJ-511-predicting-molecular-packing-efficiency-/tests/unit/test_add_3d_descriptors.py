"""
Unit tests for add_3d_descriptors.py
"""
import pytest
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from add_3d_descriptors import (
    calculate_radius_of_gyration,
    calculate_asphericity,
    calculate_principal_moments,
    generate_conformer,
    compute_3d_descriptors
)

def test_generate_conformer_valid_molecule():
    """Test that a valid SMILES generates a conformer."""
    smiles = "CCO"  # Ethanol
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None
    
    mol_3d = generate_conformer(mol)
    assert mol_3d is not None
    assert mol_3d.GetNumConformers() == 1

def test_calculate_radius_of_gyration():
    """Test radius of gyration calculation."""
    smiles = "CCO"
    mol = Chem.MolFromSmiles(smiles)
    mol_3d = generate_conformer(mol)
    
    rg = calculate_radius_of_gyration(mol_3d)
    assert isinstance(rg, float)
    assert rg > 0

def test_calculate_asphericity():
    """Test asphericity calculation."""
    smiles = "CCO"
    mol = Chem.MolFromSmiles(smiles)
    mol_3d = generate_conformer(mol)
    
    asp = calculate_asphericity(mol_3d)
    assert isinstance(asp, float)
    # Asphericity can be negative or positive depending on shape
    # but should be a finite number
    assert np.isfinite(asp)

def test_calculate_principal_moments():
    """Test principal moments calculation."""
    smiles = "CCO"
    mol = Chem.MolFromSmiles(smiles)
    mol_3d = generate_conformer(mol)
    
    m1, m2, m3 = calculate_principal_moments(mol_3d)
    assert isinstance(m1, float)
    assert isinstance(m2, float)
    assert isinstance(m3, float)
    assert m1 >= m2 >= m3  # Sorted descending
    assert m1 > 0

def test_compute_3d_descriptors():
    """Test full descriptor computation."""
    smiles = "CCO"
    descriptors = compute_3d_descriptors(smiles)
    
    assert 'radius_of_gyration' in descriptors
    assert 'asphericity' in descriptors
    assert 'principal_moment_1' in descriptors
    assert 'principal_moment_2' in descriptors
    assert 'principal_moment_3' in descriptors
    
    for key, val in descriptors.items():
        assert isinstance(val, float)
        assert np.isfinite(val)

def test_compute_3d_descriptors_invalid_smiles():
    """Test that invalid SMILES raises an error."""
    with pytest.raises(ValueError):
        compute_3d_descriptors("invalid_smiles_string")

def test_consistency_with_seed():
    """Test that results are consistent with fixed seed."""
    # This test verifies that the seed is being used correctly
    # by checking that two runs produce the same results
    smiles = "CCO"
    
    # First run
    desc1 = compute_3d_descriptors(smiles)
    
    # Second run (should be identical due to fixed seed)
    desc2 = compute_3d_descriptors(smiles)
    
    for key in desc1:
        assert desc1[key] == desc2[key], f"Mismatch in {key}: {desc1[key]} != {desc2[key]}"