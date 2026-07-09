"""
Unit tests for the data models (Molecule, DatasetSplit, Dataset).
"""
import pytest
import numpy as np
from code.models import Molecule, DatasetSplit, Dataset


class TestMolecule:
    """Tests for the Molecule class."""
    
    def test_molecule_creation(self):
        """Test basic molecule creation."""
        mol = Molecule(
            smiles="CCO",
            mol_id="test_001",
            log_s=-1.5
        )
        assert mol.smiles == "CCO"
        assert mol.mol_id == "test_001"
        assert mol.log_s == -1.5
        assert mol.atom_features is None
        
    def test_molecule_with_features(self):
        """Test molecule creation with features."""
        atom_features = np.array([[1.0, 2.0], [3.0, 4.0]])
        bond_features = np.array([[5.0, 6.0]])
        
        mol = Molecule(
            smiles="CCO",
            mol_id="test_002",
            log_s=-2.0,
            atom_features=atom_features,
            bond_features=bond_features
        )
        
        assert np.array_equal(mol.atom_features, atom_features)
        assert np.array_equal(mol.bond_features, bond_features)
        
    def test_molecule_to_dict(self):
        """Test molecule serialization to dictionary."""
        atom_features = np.array([[1.0, 2.0]])
        mol = Molecule(
            smiles="CCO",
            mol_id="test_003",
            log_s=-1.0,
            atom_features=atom_features,
            metadata={'source': 'test'}
        )
        
        result = mol.to_dict()
        
        assert result['smiles'] == "CCO"
        assert result['mol_id'] == "test_003"
        assert result['log_s'] == -1.0
        assert isinstance(result['atom_features'], list)
        assert result['metadata']['source'] == 'test'
        
    def test_molecule_from_dict(self):
        """Test molecule deserialization from dictionary."""
        data = {
            'smiles': "CCO",
            'mol_id': "test_004",
            'log_s': -1.2,
            'atom_features': [[1.0, 2.0]],
            'bond_features': [[3.0, 4.0]],
            'metadata': {'source': 'test'}
        }
        
        mol = Molecule.from_dict(data)
        
        assert mol.smiles == "CCO"
        assert mol.mol_id == "test_004"
        assert mol.log_s == -1.2
        assert isinstance(mol.atom_features, np.ndarray)
        assert mol.metadata['source'] == 'test'


class TestDatasetSplit:
    """Tests for the DatasetSplit class."""
    
    def test_split_creation(self):
        """Test basic split creation."""
        split = DatasetSplit(
            name="train",
            molecule_ids=["m1", "m2", "m3"]
        )
        
        assert split.name == "train"
        assert len(split.molecule_ids) == 3
        assert split.statistics == {}
        
    def test_split_with_log_s(self):
        """Test split creation with logS values."""
        split = DatasetSplit(
            name="test",
            molecule_ids=["m1", "m2", "m3"],
            log_s_values=[-1.0, -2.0, -3.0]
        )
        
        assert len(split.log_s_values) == 3
        assert 'mean' in split.statistics
        assert split.statistics['mean'] == -2.0
        assert split.statistics['count'] == 3
        
    def test_split_add_molecule(self):
        """Test adding a molecule to a split."""
        split = DatasetSplit(name="val", molecule_ids=[])
        
        mol = Molecule(
            smiles="CCO",
            mol_id="m1",
            log_s=-1.5
        )
        
        split.add_molecule(mol)
        
        assert "m1" in split.molecule_ids
        assert len(split.log_s_values) == 1
        assert split.statistics['mean'] == -1.5


class TestDataset:
    """Tests for the Dataset class."""
    
    def test_dataset_creation(self):
        """Test basic dataset creation."""
        dataset = Dataset()
        
        assert dataset.train is None
        assert dataset.validation is None
        assert dataset.test is None
        assert len(dataset.all_molecules) == 0
        
    def test_add_molecule(self):
        """Test adding molecules to dataset."""
        dataset = Dataset()
        
        mol = Molecule(smiles="CCO", mol_id="m1", log_s=-1.0)
        dataset.add_molecule(mol)
        
        assert "m1" in dataset.all_molecules
        assert dataset.get_molecule("m1") == mol
        
    def test_get_nonexistent_molecule(self):
        """Test retrieving a non-existent molecule."""
        dataset = Dataset()
        
        mol = dataset.get_molecule("nonexistent")
        assert mol is None
        
    def test_dataset_with_splits(self):
        """Test dataset with all splits."""
        train_split = DatasetSplit(name="train", molecule_ids=["m1"])
        test_split = DatasetSplit(name="test", molecule_ids=["m2"])
        
        dataset = Dataset(train=train_split, test=test_split)
        
        assert dataset.train.name == "train"
        assert dataset.test.name == "test"
        assert dataset.validation is None