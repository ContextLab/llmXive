"""
Unit tests for the Molecule data model.
"""
import pytest
import numpy as np
from rdkit import Chem
from code.data_models.molecule import Molecule, NODE_FEATURE_KEYS, EDGE_FEATURE_KEYS

def test_molecule_creation_from_smiles():
    """Test creating a Molecule from a valid SMILES string."""
    smiles = "CCO"  # Ethanol
    mol = Molecule.from_smiles(smiles)
    
    assert mol is not None
    assert mol.smiles == smiles
    assert mol.mol is not None
    assert mol.atom_count == 3  # 2 C, 1 O
    assert mol.molecular_weight > 0

def test_molecule_creation_invalid_smiles():
    """Test creating a Molecule from an invalid SMILES string."""
    invalid_smiles = "invalid_smiles_string"
    mol = Molecule.from_smiles(invalid_smiles)
    
    assert mol is None

def test_molecule_validate_valid():
    """Test validation of a valid molecule."""
    smiles = "CCO"
    mol = Molecule.from_smiles(smiles)
    
    assert mol.validate() is True

def test_molecule_validate_empty_smiles():
    """Test validation with empty SMILES."""
    mol = Molecule(smiles="", mol=None)
    assert mol.validate() is False

def test_molecule_validate_none_mol():
    """Test validation with None Mol object."""
    mol = Molecule(smiles="CCO", mol=None)
    assert mol.validate() is False

def test_molecule_node_features_shape():
    """Test that node features have the correct shape."""
    smiles = "CCO"
    mol = Molecule.from_smiles(smiles)
    
    expected_shape = (mol.atom_count, 3)
    assert mol.node_features.shape == expected_shape
    
    # Check feature keys
    assert len(NODE_FEATURE_KEYS) == 3
    assert set(NODE_FEATURE_KEYS) == {'atom_type', 'hybridization', 'formal_charge'}

def test_molecule_edge_features_shape():
    """Test that edge features have the correct shape."""
    smiles = "CCO"
    mol = Molecule.from_smiles(smiles)
    
    expected_shape = (mol.mol.GetNumBonds(), 3)
    assert mol.edge_features.shape == expected_shape
    
    # Check feature keys
    assert len(EDGE_FEATURE_KEYS) == 3
    assert set(EDGE_FEATURE_KEYS) == {'bond_type', 'conjugated', 'aromatic'}

def test_molecule_to_dict():
    """Test conversion to dictionary."""
    smiles = "CCO"
    mol = Molecule.from_smiles(smiles)
    
    data = mol.to_dict()
    
    assert 'smiles' in data
    assert 'molecular_weight' in data
    assert 'atom_count' in data
    assert 'node_features' in data
    assert 'edge_features' in data
    
    # Check types
    assert isinstance(data['smiles'], str)
    assert isinstance(data['molecular_weight'], float)
    assert isinstance(data['atom_count'], int)
    assert isinstance(data['node_features'], list)
    assert isinstance(data['edge_features'], list)

def test_molecule_node_features_content():
    """Test that node features contain valid data."""
    smiles = "CCO"
    mol = Molecule.from_smiles(smiles)
    
    # Check that features are not empty
    assert mol.node_features.size > 0
    
    # Check that first column (atom_type) contains atomic numbers
    atom_types = mol.node_features[:, 0]
    assert all(atom_types > 0)  # Atomic numbers are positive

def test_molecule_edge_features_content():
    """Test that edge features contain valid data."""
    smiles = "CCO"
    mol = Molecule.from_smiles(smiles)
    
    if mol.mol.GetNumBonds() > 0:
        assert mol.edge_features.size > 0
        
        # Check bond types (should be integers)
        bond_types = mol.edge_features[:, 0]
        assert all(bond_types >= 0)

def test_molecule_manual_creation():
    """Test creating a Molecule manually with all attributes."""
    smiles = "CC"
    mol_obj = Chem.MolFromSmiles(smiles)
    
    mol = Molecule(
        smiles=smiles,
        mol=mol_obj,
        molecular_weight=30.0,
        atom_count=2,
        node_features=np.array([[6.0, 3.0, 0.0], [6.0, 3.0, 0.0]]),
        edge_features=np.array([[1.0, 0.0, 0.0]])
    )
    
    assert mol.validate() is True
    assert mol.molecular_weight == 30.0
    assert mol.atom_count == 2