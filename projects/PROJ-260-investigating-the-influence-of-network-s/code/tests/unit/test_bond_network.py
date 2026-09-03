"""
Unit tests for the BondNetwork class.

These tests verify:
- Correct initialization and validation
- Accurate coordination number calculation
- Bond angle variance computation
- Global metrics calculation
- Physical constraint validation
"""

import numpy as np
import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.bond_network import BondNetwork

def test_valid_initialization():
    """Test that a valid network initializes without errors."""
    positions = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ])
    atom_ids = [0, 1, 2, 3]
    
    network = BondNetwork(atom_ids=atom_ids, positions=positions, cutoff=1.5)
    
    assert len(network.atom_ids) == 4
    assert len(network.coordination_numbers) == 4
    assert network.is_valid

def test_coordination_number_calculation():
    """Test that coordination numbers are calculated correctly."""
    # Create a simple linear chain: 0-1-2-3
    positions = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [3.0, 0.0, 0.0],
    ])
    atom_ids = [0, 1, 2, 3]
    
    # Cutoff should be > 1.0 but < 2.0 to only connect adjacent atoms
    network = BondNetwork(atom_ids=atom_ids, positions=positions, cutoff=1.5)
    
    # Expected coordination: [1, 2, 2, 1]
    expected_coords = [1, 2, 2, 1]
    assert network.coordination_numbers == expected_coords

def test_coordination_with_cluster():
    """Test coordination on a small cluster (manual calculation)."""
    # Create a central atom with 4 neighbors (tetrahedral-like)
    # Central atom at origin, neighbors at distance 1.0
    positions = np.array([
        [0.0, 0.0, 0.0],  # Central
        [1.0, 0.0, 0.0],  # Neighbor 1
        [0.0, 1.0, 0.0],  # Neighbor 2
        [0.0, 0.0, 1.0],  # Neighbor 3
        [0.5, 0.5, 0.5],  # Neighbor 4 (closer)
    ])
    atom_ids = [0, 1, 2, 3, 4]
    
    # Cutoff = 1.2 to include all neighbors of central atom
    network = BondNetwork(atom_ids=atom_ids, positions=positions, cutoff=1.2)
    
    # Central atom (index 0) should have coordination 4
    # Neighbors should have coordination 1 (only connected to center)
    # Except neighbor 4 which is closer to center
    assert network.coordination_numbers[0] == 4
    # Check that neighbors have at least 1 connection
    for i in range(1, 5):
        assert network.coordination_numbers[i] >= 1

def test_bond_angle_variance():
    """Test bond angle variance calculation."""
    # Create atoms with known angles
    # Central atom with 3 neighbors at 120 degrees (planar)
    positions = np.array([
        [0.0, 0.0, 0.0],  # Central
        [1.0, 0.0, 0.0],  # Neighbor 1
        [-0.5, np.sqrt(3)/2, 0.0],  # Neighbor 2 (120 deg)
        [-0.5, -np.sqrt(3)/2, 0.0], # Neighbor 3 (240 deg)
    ])
    atom_ids = [0, 1, 2, 3]
    
    network = BondNetwork(atom_ids=atom_ids, positions=positions, cutoff=1.5)
    
    # The angles between neighbors should be 120 degrees (2π/3 radians)
    # Variance of three 120-degree angles should be 0
    # (Note: due to floating point, it might not be exactly 0)
    assert network.bond_angle_variances[0] < 0.01  # Small tolerance

def test_invalid_positions_shape():
    """Test that invalid position shapes raise errors."""
    with pytest.raises(ValueError):
        BondNetwork(
            atom_ids=[0, 1],
            positions=np.array([[0.0, 0.0]]),  # 2D, not 3D
            cutoff=1.5
        )

def test_invalid_atom_id_count():
    """Test that mismatched atom_ids and positions raise errors."""
    with pytest.raises(ValueError):
        BondNetwork(
            atom_ids=[0, 1, 2],  # 3 IDs
            positions=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),  # 2 positions
            cutoff=1.5
        )

def test_global_metrics():
    """Test global metrics calculation."""
    positions = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ])
    atom_ids = [0, 1, 2, 3]
    
    network = BondNetwork(atom_ids=atom_ids, positions=positions, cutoff=1.5)
    metrics = network.get_global_metrics()
    
    assert "avg_coordination" in metrics
    assert "max_coordination" in metrics
    assert "total_bonds" in metrics
    assert "density" in metrics
    assert metrics["total_bonds"] > 0

def test_physical_constraint_validation():
    """Test validation of physical constraints."""
    # Create a network with an over-coordinated atom
    positions = np.array([
        [0.0, 0.0, 0.0],
        [0.5, 0.0, 0.0],
        [-0.5, 0.0, 0.0],
        [0.0, 0.5, 0.0],
        [0.0, -0.5, 0.0],
        [0.0, 0.0, 0.5],
        [0.0, 0.0, -0.5],
    ])
    atom_ids = [0, 1, 2, 3, 4, 5, 6]
    
    # Cutoff large enough to connect all to center
    network = BondNetwork(atom_ids=atom_ids, positions=positions, cutoff=1.0)
    
    # Validate with max_coord=6
    is_valid = network.validate_physical_constraints(max_coord=6)
    assert not is_valid
    assert len(network.validation_errors) > 0
    assert "coordination 6" in network.validation_errors[0] or "coordination 7" in network.validation_errors[0]

def test_to_dict_and_from_dict():
    """Test serialization and deserialization."""
    positions = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
    ])
    atom_ids = [0, 1]
    
    network = BondNetwork(atom_ids=atom_ids, positions=positions, cutoff=1.5)
    
    # Serialize
    data = network.to_dict()
    
    # Deserialize
    network2 = BondNetwork.from_dict(data)
    
    assert np.array_equal(network2.positions, network.positions)
    assert network2.atom_ids == network.atom_ids
    assert network2.coordination_numbers == network.coordination_numbers

def test_pbc_application():
    """Test that periodic boundary conditions are applied correctly."""
    # Create a box with PBC
    box_vectors = np.eye(3) * 2.0
    positions = np.array([
        [0.0, 0.0, 0.0],
        [1.9, 0.0, 0.0],  # Close to boundary
    ])
    atom_ids = [0, 1]
    
    network = BondNetwork(
        atom_ids=atom_ids, 
        positions=positions, 
        box_vectors=box_vectors,
        cutoff=0.5  # Small cutoff, but PBC should make them close
    )
    
    # With PBC, distance between (0,0,0) and (1.9,0,0) in a 2.0 box
    # should be min(|1.9-0|, |1.9-2.0|) = 0.1
    # So they should be connected if cutoff > 0.1
    assert 1 in network.adjacency[0]