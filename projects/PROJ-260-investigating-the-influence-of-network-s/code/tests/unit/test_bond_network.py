"""
Unit tests for the BondNetwork model.
"""
import numpy as np
import pytest
import sys
import os

from src.models.bond_network import BondNetwork
from src.models.simulation_box import SimulationBox


def test_valid_initialization():
    """Test that a BondNetwork can be initialized with valid data."""
    num_atoms = 10
    positions = np.random.rand(num_atoms, 3)
    box_vectors = np.eye(3) * 10.0
    cutoff = 3.0
    
    network = BondNetwork(
        num_atoms=num_atoms,
        atom_ids=np.arange(num_atoms),
        positions=positions,
        box_vectors=box_vectors,
        cutoff=cutoff
    )
    
    assert network.num_atoms == num_atoms
    assert network.cutoff == cutoff
    assert network.positions.shape == (num_atoms, 3)
    assert network.box_vectors.shape == (3, 3)
    assert network.is_valid is True


def test_coordination_number_calculation():
    """Test coordination number calculation for a simple cluster."""
    # Create a central atom at origin and 4 neighbors at distance 2.0
    # Cutoff is 2.5, so all 4 should be neighbors.
    num_atoms = 5
    positions = np.zeros((num_atoms, 3))
    positions[0] = [0, 0, 0]
    positions[1] = [2, 0, 0]
    positions[2] = [-2, 0, 0]
    positions[3] = [0, 2, 0]
    positions[4] = [0, -2, 0]
    
    box_vectors = np.eye(3) * 10.0
    cutoff = 2.5
    
    network = BondNetwork(
        num_atoms=num_atoms,
        atom_ids=np.arange(num_atoms),
        positions=positions,
        box_vectors=box_vectors,
        cutoff=cutoff
    )
    
    network.compute_adjacency()
    
    # Atom 0 should have coordination 4
    assert network.coordination_numbers[0] == 4
    # Other atoms should have coordination 1 (only connected to 0)
    assert network.coordination_numbers[1] == 1
    assert network.coordination_numbers[2] == 1
    assert network.coordination_numbers[3] == 1
    assert network.coordination_numbers[4] == 1


def test_coordination_with_cluster():
    """Test coordination on a slightly larger, more complex cluster."""
    # Tetrahedral arrangement approx
    num_atoms = 5
    positions = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
        [1.0, -1.0, -1.0],
        [-1.0, 1.0, -1.0],
        [-1.0, -1.0, 1.0]
    ])
    # Distances from center are sqrt(3) ~ 1.732
    # Distance between neighbors: sqrt(8) ~ 2.828
    
    box_vectors = np.eye(3) * 10.0
    cutoff = 2.0 # Should catch center to neighbors, but not neighbor to neighbor
    
    network = BondNetwork(
        num_atoms=num_atoms,
        atom_ids=np.arange(num_atoms),
        positions=positions,
        box_vectors=box_vectors,
        cutoff=cutoff
    )
    
    network.compute_adjacency()
    
    # Center (0) connected to 4
    assert network.coordination_numbers[0] == 4
    # Neighbors only connected to center
    assert all(network.coordination_numbers[1:] == 1)


def test_bond_angle_variance():
    """Test bond angle variance calculation."""
    # Atom 0 at origin.
    # Neighbors at 0, 1, 2 on x-axis: angles 0, 0 (collinear) -> variance 0
    # Neighbors at 0, 1, 2 forming a triangle: angles 60, 60, 60 -> variance 0
    # Neighbors at 0, 1, 2 forming 90, 90, 180 -> variance > 0
    
    num_atoms = 4
    positions = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ])
    # Center at 0. Neighbors at 1, 2, 3.
    # Angles: (1,2) -> 90 deg, (1,3) -> 90 deg, (2,3) -> 90 deg.
    # Variance of [90, 90, 90] is 0.
    
    box_vectors = np.eye(3) * 10.0
    cutoff = 2.0
    
    network = BondNetwork(
        num_atoms=num_atoms,
        atom_ids=np.arange(num_atoms),
        positions=positions,
        box_vectors=box_vectors,
        cutoff=cutoff
    )
    
    network.compute_adjacency()
    network.compute_bond_angle_variance()
    
    # All angles 90 degrees (pi/2). Variance should be 0.
    assert np.isclose(network.bond_angle_variances[0], 0.0)
    
    # Atom 1 has only 1 neighbor (0). Variance should be 0.
    assert np.isclose(network.bond_angle_variances[1], 0.0)


def test_invalid_positions_shape():
    """Test initialization fails with invalid position shape."""
    with pytest.raises(ValueError):
        BondNetwork(
            num_atoms=3,
            atom_ids=np.arange(3),
            positions=np.zeros((3, 2)), # 2D positions
            box_vectors=np.eye(3),
            cutoff=1.0
        )


def test_invalid_atom_id_count():
    """Test initialization fails if atom_ids count mismatches num_atoms."""
    with pytest.raises(ValueError):
        BondNetwork(
            num_atoms=3,
            atom_ids=np.arange(2), # Count mismatch
            positions=np.zeros((3, 3)),
            box_vectors=np.eye(3),
            cutoff=1.0
        )


def test_global_metrics():
    """Test calculation of global metrics."""
    num_atoms = 4
    positions = np.array([
        [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
    ])
    box_vectors = np.eye(3) * 10.0
    cutoff = 2.0
    
    network = BondNetwork(
        num_atoms=num_atoms,
        atom_ids=np.arange(num_atoms),
        positions=positions,
        box_vectors=box_vectors,
        cutoff=cutoff
    )
    
    network.compute_adjacency()
    network.validate_physical_constraints()
    
    assert 'average_coordination' in network.global_metrics
    assert 'total_bonds' in network.global_metrics
    assert 'density' in network.global_metrics
    
    # Total bonds: 0-1, 0-2, 0-3 -> 3 bonds
    assert network.global_metrics['total_bonds'] == 3


def test_physical_constraint_validation():
    """Test anomaly flagging for high coordination."""
    # Create a scenario with high coordination
    num_atoms = 8
    positions = np.zeros((num_atoms, 3))
    # Central atom at 0
    # 7 neighbors very close
    for i in range(1, 8):
        positions[i] = [0.1 * i, 0, 0] # All within 0.7 distance
        
    box_vectors = np.eye(3) * 10.0
    cutoff = 1.0
    
    network = BondNetwork(
        num_atoms=num_atoms,
        atom_ids=np.arange(num_atoms),
        positions=positions,
        box_vectors=box_vectors,
        cutoff=cutoff
    )
    
    network.compute_adjacency()
    network.validate_physical_constraints()
    
    # Atom 0 has 7 neighbors -> anomaly
    assert 0 in network.anomaly_flags
    assert any("High coordination" in flag for flag in network.anomaly_flags[0])
    assert network.is_valid is False # Network contains anomalies


def test_to_dict_and_from_dict():
    """Test serialization and deserialization."""
    num_atoms = 3
    positions = np.random.rand(3, 3)
    box_vectors = np.eye(3) * 5.0
    cutoff = 2.0
    
    network = BondNetwork(
        num_atoms=num_atoms,
        atom_ids=np.arange(num_atoms),
        positions=positions,
        box_vectors=box_vectors,
        cutoff=cutoff
    )
    network.compute_adjacency()
    network.compute_bond_angle_variance()
    network.validate_physical_constraints()
    
    data = network.to_dict()
    
    # Reconstruct (partial)
    reconstructed = BondNetwork.from_dict(data)
    
    assert reconstructed.num_atoms == network.num_atoms
    assert reconstructed.cutoff == network.cutoff
    assert np.array_equal(reconstructed.coordination_numbers, network.coordination_numbers)
    assert np.allclose(reconstructed.bond_angle_variances, network.bond_angle_variances)
    assert reconstructed.is_valid == network.is_valid


def test_pbc_application():
    """Test that Minimum Image Convention is applied correctly."""
    # Box size 10. Atom at 0.9, Atom at 9.1.
    # Distance should be 1.8 (via PBC), not 8.2.
    num_atoms = 2
    positions = np.array([
        [0.9, 0.0, 0.0],
        [9.1, 0.0, 0.0]
    ])
    box_vectors = np.eye(3) * 10.0
    cutoff = 2.0
    
    network = BondNetwork(
        num_atoms=num_atoms,
        atom_ids=np.arange(num_atoms),
        positions=positions,
        box_vectors=box_vectors,
        cutoff=cutoff
    )
    
    network.compute_adjacency()
    
    # Should be bonded because distance is 1.8
    assert network.coordination_numbers[0] == 1
    assert network.coordination_numbers[1] == 1
    assert len(network.edges) == 1