"""
Unit tests for the SimulationBox data class.
"""
import numpy as np
import pytest
import sys
import os
from src.models.simulation_box import SimulationBox


def test_valid_initialization():
    """Test that a SimulationBox can be initialized with valid data."""
    atom_ids = [1, 2, 3]
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    
    box = SimulationBox(atom_ids=atom_ids, positions=positions)
    
    assert len(box) == 3
    assert np.array_equal(box.atom_ids, atom_ids)
    assert np.array_equal(box.positions, positions)
    assert box.velocities is None
    assert box.box_vectors is None


def test_initialization_with_velocities():
    """Test initialization with velocities."""
    atom_ids = [1, 2]
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    velocities = np.array([[0.1, 0.0, 0.0], [0.0, 0.1, 0.0]])
    
    box = SimulationBox(atom_ids=atom_ids, positions=positions, velocities=velocities)
    
    assert box.velocities is not None
    assert np.array_equal(box.velocities, velocities)


def test_initialization_with_thermal_conductivity():
    """Test initialization with thermal conductivity."""
    atom_ids = [1]
    positions = np.array([[0.0, 0.0, 0.0]])
    
    box = SimulationBox(
        atom_ids=atom_ids, 
        positions=positions, 
        thermal_conductivity=1.5
    )
    
    assert box.thermal_conductivity == 1.5


def test_invalid_position_shape():
    """Test that invalid position shapes raise ValueError."""
    atom_ids = [1, 2]
    positions = np.array([[0.0, 0.0]])  # Missing Z dimension
    
    with pytest.raises(ValueError):
        SimulationBox(atom_ids=atom_ids, positions=positions)


def test_invalid_velocity_shape():
    """Test that mismatched velocity shapes raise ValueError."""
    atom_ids = [1, 2]
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    velocities = np.array([[0.1, 0.0]])  # Wrong shape
    
    with pytest.raises(ValueError):
        SimulationBox(atom_ids=atom_ids, positions=positions, velocities=velocities)


def test_invalid_atom_id_count():
    """Test that mismatched atom_id count raises ValueError."""
    atom_ids = [1, 2, 3]
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])  # Only 2 positions
    
    with pytest.raises(ValueError):
        SimulationBox(atom_ids=atom_ids, positions=positions)


def test_invalid_box_vectors_shape():
    """Test that invalid box_vectors shape raises ValueError."""
    atom_ids = [1]
    positions = np.array([[0.0, 0.0, 0.0]])
    box_vectors = np.array([[1.0, 0.0]])  # Wrong shape
    
    with pytest.raises(ValueError):
        SimulationBox(atom_ids=atom_ids, positions=positions, box_vectors=box_vectors)


def test_to_dict_and_from_dict():
    """Test serialization and deserialization."""
    atom_ids = [1, 2]
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    velocities = np.array([[0.1, 0.0, 0.0], [0.0, 0.1, 0.0]])
    box_vectors = np.eye(3) * 10.0
    metadata = {"temperature": 300.0, "system": "a-Si"}
    
    original_box = SimulationBox(
        atom_ids=atom_ids,
        positions=positions,
        velocities=velocities,
        box_vectors=box_vectors,
        metadata=metadata,
        thermal_conductivity=2.5
    )
    
    # Serialize
    data = original_box.to_dict()
    
    # Deserialize
    restored_box = SimulationBox.from_dict(data)
    
    # Verify
    assert len(restored_box) == len(original_box)
    assert np.allclose(restored_box.positions, original_box.positions)
    assert np.allclose(restored_box.velocities, original_box.velocities)
    assert np.allclose(restored_box.box_vectors, original_box.box_vectors)
    assert restored_box.metadata == original_box.metadata
    assert restored_box.thermal_conductivity == original_box.thermal_conductivity


def test_get_kinetic_energy_no_velocities():
    """Test that get_kinetic_energy returns None when velocities are missing."""
    atom_ids = [1]
    positions = np.array([[0.0, 0.0, 0.0]])
    box = SimulationBox(atom_ids=atom_ids, positions=positions)
    
    assert box.get_kinetic_energy() is None


def test_get_kinetic_energy_with_velocities():
    """Test kinetic energy calculation with velocities."""
    atom_ids = [1, 2]
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    velocities = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    box = SimulationBox(atom_ids=atom_ids, positions=positions, velocities=velocities)
    
    # KE = 0.5 * sum(v^2) = 0.5 * (1 + 1) = 1.0
    expected_ke = 1.0
    assert np.isclose(box.get_kinetic_energy(), expected_ke)
