"""
Unit tests for the SimulationBox data class.
"""

import numpy as np
import pytest
import sys
import os

# Ensure the src directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.models.simulation_box import SimulationBox


def test_valid_initialization():
    """Test that a valid SimulationBox is created correctly."""
    n = 4
    atom_ids = list(range(n))
    positions = np.random.rand(n, 3)
    box_vectors = np.eye(3) * 10.0
    
    box = SimulationBox(
        atom_ids=atom_ids,
        positions=positions,
        box_vectors=box_vectors,
        system_size=n
    )
    
    assert box.system_size == n
    assert box.positions.shape == (n, 3)
    assert len(box.atom_ids) == n
    assert box.velocities is None
    assert box.thermal_conductivity is None


def test_initialization_with_velocities():
    """Test initialization with velocities."""
    n = 4
    atom_ids = list(range(n))
    positions = np.random.rand(n, 3)
    velocities = np.random.rand(n, 3)
    box_vectors = np.eye(3) * 10.0
    
    box = SimulationBox(
        atom_ids=atom_ids,
        positions=positions,
        velocities=velocities,
        box_vectors=box_vectors,
        system_size=n
    )
    
    assert box.velocities.shape == (n, 3)
    assert np.array_equal(box.velocities, velocities)


def test_initialization_with_thermal_conductivity():
    """Test initialization with thermal conductivity."""
    n = 4
    atom_ids = list(range(n))
    positions = np.random.rand(n, 3)
    box_vectors = np.eye(3) * 10.0
    kappa = 1.5
    
    box = SimulationBox(
        atom_ids=atom_ids,
        positions=positions,
        box_vectors=box_vectors,
        system_size=n,
        thermal_conductivity=kappa
    )
    
    assert box.thermal_conductivity == kappa


def test_invalid_position_shape():
    """Test that invalid position shape raises ValueError."""
    n = 4
    atom_ids = list(range(n))
    # Wrong shape: (n, 2) instead of (n, 3)
    positions = np.random.rand(n, 2)
    box_vectors = np.eye(3) * 10.0
    
    with pytest.raises(ValueError, match="Positions shape"):
        SimulationBox(
            atom_ids=atom_ids,
            positions=positions,
            box_vectors=box_vectors,
            system_size=n
        )


def test_invalid_velocity_shape():
    """Test that invalid velocity shape raises ValueError."""
    n = 4
    atom_ids = list(range(n))
    positions = np.random.rand(n, 3)
    velocities = np.random.rand(n, 2) # Wrong shape
    box_vectors = np.eye(3) * 10.0
    
    with pytest.raises(ValueError, match="Velocities shape"):
        SimulationBox(
            atom_ids=atom_ids,
            positions=positions,
            velocities=velocities,
            box_vectors=box_vectors,
            system_size=n
        )


def test_invalid_atom_id_count():
    """Test that mismatched atom_id count raises ValueError."""
    n = 4
    atom_ids = [1, 2] # Only 2 IDs
    positions = np.random.rand(n, 3)
    box_vectors = np.eye(3) * 10.0
    
    with pytest.raises(ValueError, match="Number of atom_ids"):
        SimulationBox(
            atom_ids=atom_ids,
            positions=positions,
            box_vectors=box_vectors,
            system_size=n
        )


def test_invalid_box_vectors_shape():
    """Test that invalid box_vectors shape raises ValueError."""
    n = 4
    atom_ids = list(range(n))
    positions = np.random.rand(n, 3)
    box_vectors = np.eye(3) # Correct shape is (3, 3), this is (3, 3) but let's try (2, 3)
    box_vectors_bad = np.eye(3)[:2, :]
    
    with pytest.raises(ValueError, match="Box vectors must be"):
        SimulationBox(
            atom_ids=atom_ids,
            positions=positions,
            box_vectors=box_vectors_bad,
            system_size=n
        )


def test_to_dict_and_from_dict():
    """Test serialization and deserialization."""
    n = 4
    atom_ids = list(range(n))
    positions = np.random.rand(n, 3)
    velocities = np.random.rand(n, 3)
    box_vectors = np.eye(3) * 10.0
    kappa = 1.23
    metadata = {"temperature": 300, "ensemble": "NVT"}
    
    original = SimulationBox(
        atom_ids=atom_ids,
        positions=positions,
        velocities=velocities,
        box_vectors=box_vectors,
        system_size=n,
        thermal_conductivity=kappa,
        metadata=metadata
    )
    
    data = original.to_dict()
    reconstructed = SimulationBox.from_dict(data)
    
    assert reconstructed.system_size == n
    assert np.allclose(reconstructed.positions, positions)
    assert np.allclose(reconstructed.velocities, velocities)
    assert reconstructed.thermal_conductivity == kappa
    assert reconstructed.metadata == metadata


def test_get_kinetic_energy_no_velocities():
    """Test kinetic energy calculation when velocities are None."""
    n = 4
    atom_ids = list(range(n))
    positions = np.random.rand(n, 3)
    box_vectors = np.eye(3) * 10.0
    
    box = SimulationBox(
        atom_ids=atom_ids,
        positions=positions,
        box_vectors=box_vectors,
        system_size=n
    )
    
    assert box.get_kinetic_energy() == 0.0


def test_get_kinetic_energy_with_velocities():
    """Test kinetic energy calculation with velocities."""
    n = 4
    atom_ids = list(range(n))
    positions = np.random.rand(n, 3)
    velocities = np.ones((n, 3)) # All velocities = 1.0
    box_vectors = np.eye(3) * 10.0
    
    box = SimulationBox(
        atom_ids=atom_ids,
        positions=positions,
        velocities=velocities,
        box_vectors=box_vectors,
        system_size=n
    )
    
    # E_k = 0.5 * sum(v^2) = 0.5 * 4 * 3 * 1^2 = 6.0
    expected_ke = 0.5 * np.sum(velocities ** 2)
    assert box.get_kinetic_energy() == pytest.approx(expected_ke)