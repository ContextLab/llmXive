import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from rdkit import Chem

from code.data.preprocess import (
    calculate_molecular_weight,
    extract_2d_features,
    process_molecule_2d,
    process_chunk_2d,
    MAX_ATOMS
)

def test_calculate_molecular_weight():
    """Test molecular weight calculation."""
    mol = Chem.MolFromSmiles("CCO")  # Ethanol
    assert mol is not None
    mw = calculate_molecular_weight(mol)
    assert isinstance(mw, float)
    assert mw > 0
    # Ethanol MW is approximately 46.07
    assert 45.0 < mw < 47.0

def test_extract_2d_features():
    """Test 2D feature extraction."""
    mol = Chem.MolFromSmiles("CCO")
    assert mol is not None
    
    node_features, edge_features = extract_2d_features(mol)
    
    # Should have 3 atoms (2 C, 1 O)
    assert len(node_features) == 3
    
    # Each node feature should be [atomic_num, hybridization, charge]
    for feature in node_features:
        assert len(feature) == 3
        assert isinstance(feature[0], float)  # atomic number
        assert isinstance(feature[1], float)  # hybridization
        assert isinstance(feature[2], float)  # charge
    
    # Should have edges (C-C and C-O bonds)
    assert len(edge_features) >= 2

def test_process_molecule_2d_valid():
    """Test processing a valid small molecule."""
    smiles = "CCO"
    result = process_molecule_2d(smiles)
    
    assert result is not None
    assert result['smiles'] == smiles
    assert 'node_features' in result
    assert 'edge_features' in result
    assert 'molecular_weight' in result
    assert 'atom_count' in result
    assert result['atom_count'] <= MAX_ATOMS

def test_process_molecule_2d_invalid_smiles():
    """Test processing an invalid SMILES string."""
    smiles = "invalid_smiles_string"
    result = process_molecule_2d(smiles)
    assert result is None

def test_process_molecule_2d_too_many_atoms():
    """Test that molecules with too many atoms are excluded."""
    # Create a very long chain
    smiles = "C" * 150  # 150 carbons
    result = process_molecule_2d(smiles)
    assert result is None

def test_process_chunk_2d():
    """Test chunk processing."""
    data = {
        'smiles': ['CCO', 'CC', 'CCCC', 'invalid', 'C' * 150]
    }
    df = pd.DataFrame(data)
    
    processed_df, excluded_count = process_chunk_2d(df)
    
    # Should have 3 valid molecules (CCO, CC, CCCC)
    # 1 invalid SMILES, 1 too many atoms
    assert len(processed_df) == 3
    assert excluded_count >= 1  # At least the one with too many atoms
    
    # Check columns
    assert 'smiles' in processed_df.columns
    assert 'node_features' in processed_df.columns
    assert 'edge_features' in processed_df.columns
    assert 'molecular_weight' in processed_df.columns

def test_max_atoms_filter():
    """Test that MAX_ATOMS constant is used."""
    assert MAX_ATOMS == 100