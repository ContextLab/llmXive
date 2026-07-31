import pytest
import numpy as np
from rdkit import Chem
from code.data.preprocess import (
    get_atom_features,
    get_edge_features,
    molecule_to_graph,
    process_molecule_2d,
    calculate_molecular_weight
)

def test_get_atom_features():
    """Test atom feature extraction for a carbon atom."""
    mol = Chem.MolFromSmiles("CC")
    atom = mol.GetAtomWithIdx(0)
    features = get_atom_features(atom)
    assert features.shape[0] > 0
    assert np.sum(features) == 3.0  # One-hot for type, hyb, charge

def test_get_edge_features():
    """Test edge feature extraction for a single bond."""
    mol = Chem.MolFromSmiles("CC")
    bond = mol.GetBondWithIdx(0)
    features = get_edge_features(bond)
    assert features.shape[0] > 0
    assert np.sum(features) == 2.0  # One-hot for type, stereo

def test_molecule_to_graph():
    """Test graph conversion for ethane."""
    mol = Chem.MolFromSmiles("CC")
    node_feat, edge_feat, adj = molecule_to_graph(mol)
    assert node_feat.shape[0] == 2
    assert edge_feat.shape[0] == 1
    assert adj.shape == (2, 2)
    assert adj[0, 1] == 1.0
    assert adj[1, 0] == 1.0

def test_calculate_molecular_weight():
    """Test MW calculation for methane (CH4, ~16.04)."""
    mol = Chem.MolFromSmiles("C")
    mw = calculate_molecular_weight(mol)
    assert 16.0 < mw < 16.1

def test_process_molecule_2d():
    """Test full processing pipeline for a valid molecule."""
    smiles = "CCO"
    mol = Chem.MolFromSmiles(smiles)
    result = process_molecule_2d(smiles, mol)
    assert result is not None
    assert result['smiles'] == smiles
    assert 'node_features' in result
    assert 'edge_features' in result
    assert 'molecular_weight' in result
    assert result['molecular_weight'] > 0

def test_process_molecule_2d_invalid():
    """Test processing of an invalid SMILES."""
    smiles = "invalid_smiles"
    mol = Chem.MolFromSmiles(smiles)
    result = process_molecule_2d(smiles, mol)
    assert result is None