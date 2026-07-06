"""
Unit tests for the AtomicConfiguration dataclass.
"""
import pytest
import numpy as np
from code.models.atomic_config import AtomicConfiguration

def test_create_valid_configuration():
    """Test creation of a valid AtomicConfiguration."""
    positions = np.array([
        [0.0, 0.0, 0.0],
        [2.35, 0.0, 0.0],
        [0.0, 2.35, 0.0],
        [0.0, 0.0, 2.35]
    ])
    species = ['Si', 'Si', 'Si', 'Si']
    
    config = AtomicConfiguration(
        config_id="test-001",
        positions=positions,
        species=species,
        source="test-source"
    )
    
    assert config.config_id == "test-001"
    assert config.n_atoms == 4
    assert config.species == species
    assert config.source == "test-source"

def test_positions_shape_validation():
    """Test that invalid position shapes raise ValueError."""
    # 1D array should fail
    with pytest.raises(ValueError):
        AtomicConfiguration(
            config_id="fail-1",
            positions=np.array([1.0, 2.0, 3.0]),
            species=['Si']
        )
    
    # Wrong second dimension should fail
    with pytest.raises(ValueError):
        AtomicConfiguration(
            config_id="fail-2",
            positions=np.array([[1.0, 2.0]]),
            species=['Si']
        )

def test_species_length_mismatch():
    """Test that species length mismatch raises ValueError."""
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    # Only one species for two atoms
    with pytest.raises(ValueError):
        AtomicConfiguration(
            config_id="fail-3",
            positions=positions,
            species=['Si']
        )

def test_n_atoms_property():
    """Test the n_atoms property."""
    positions = np.random.rand(100, 3)
    species = ['Si'] * 100
    
    config = AtomicConfiguration(
        config_id="test-n",
        positions=positions,
        species=species
    )
    
    assert config.n_atoms == 100

def test_atomic_numbers():
    """Test conversion of species to atomic numbers."""
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    species = ['Si', 'Si']
    
    config = AtomicConfiguration(
        config_id="test-nums",
        positions=positions,
        species=species
    )
    
    expected = np.array([14, 14])
    np.testing.assert_array_equal(config.atomic_numbers, expected)

def test_get_element_counts():
    """Test element counting."""
    positions = np.array([[0.0, 0.0, 0.0]] * 10)
    species = ['Si'] * 8 + ['C'] * 2
    
    config = AtomicConfiguration(
        config_id="test-counts",
        positions=positions,
        species=species
    )
    
    counts = config.get_element_counts()
    assert counts['SI'] == 8
    assert counts['C'] == 2

def test_to_dict_and_from_dict():
    """Test serialization and deserialization."""
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    species = ['Si', 'Si']
    box_size = (10.0, 10.0, 10.0)
    
    original = AtomicConfiguration(
        config_id="test-ser",
        positions=positions,
        species=species,
        box_size=box_size,
        source="test-source",
        metadata={"key": "value"}
    )
    
    data = original.to_dict()
    restored = AtomicConfiguration.from_dict(data)
    
    assert restored.config_id == original.config_id
    assert restored.n_atoms == original.n_atoms
    assert restored.source == original.source
    assert restored.metadata == original.metadata
    np.testing.assert_array_equal(restored.positions, original.positions)

def test_repr():
    """Test string representation."""
    positions = np.array([[0.0, 0.0, 0.0]])
    species = ['Si']
    
    config = AtomicConfiguration(
        config_id="test-repr",
        positions=positions,
        species=species,
        source="test"
    )
    
    rep = repr(config)
    assert "AtomicConfiguration" in rep
    assert "test-repr" in rep
    assert "n_atoms=1" in rep