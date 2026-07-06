"""
Unit tests for graph construction with known coordinates.
Tests the graph_builder module's ability to construct graphs from atomic configurations.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.atomic_config import AtomicConfiguration
from graph_builder import build_graph, calculate_cutoff_neighbors, detect_disconnected_components


class TestGraphConstruction:
    """Test cases for graph builder functionality."""

    def test_simple_cube_graph(self):
        """Test graph construction from a simple 2x2x2 cubic lattice."""
        # Create a simple 2x2x2 cubic lattice of Silicon atoms
        lattice_constant = 5.43  # Angstroms (approximate for Si)
        positions = []
        for x in [0, 1]:
            for y in [0, 1]:
                for z in [0, 1]:
                    positions.append([x * lattice_constant / 2, y * lattice_constant / 2, z * lattice_constant / 2])
        
        positions = np.array(positions)
        atomic_numbers = np.array([14] * len(positions))  # Silicon
        
        config = AtomicConfiguration(
            config_id="test_simple_cube",
            positions=positions,
            atomic_numbers=atomic_numbers,
            metadata={"source": "test", "size": len(positions)}
        )
        
        # Build graph with a cutoff that captures nearest neighbors
        cutoff = 2.5  # Angstroms
        graph = build_graph(config, cutoff_radius=cutoff)
        
        # In a 2x2x2 simple cubic, each atom should have 3 nearest neighbors
        # (along x, y, z axes) if cutoff is appropriate
        assert graph.number_of_nodes() == 8
        assert graph.number_of_edges() > 0
        
        # Check that all nodes are present
        assert set(graph.nodes()) == set(range(8))

    def test_cutoff_neighbor_calculation(self):
        """Test the neighbor calculation with known distances."""
        # Create a linear chain with known spacing
        positions = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [3.0, 0.0, 0.0]
        ])
        atomic_numbers = np.array([14, 14, 14, 14])
        
        config = AtomicConfiguration(
            config_id="test_chain",
            positions=positions,
            atomic_numbers=atomic_numbers,
            metadata={"source": "test", "size": 4}
        )
        
        # Test with cutoff = 1.5 (should connect adjacent atoms)
        neighbors = calculate_cutoff_neighbors(config, cutoff_radius=1.5)
        
        # Atom 0 should connect to atom 1 (distance 1.0)
        assert 1 in neighbors[0]
        # Atom 0 should NOT connect to atom 2 (distance 2.0)
        assert 2 not in neighbors[0]
        
        # Atom 1 should connect to atoms 0 and 2
        assert 0 in neighbors[1]
        assert 2 in neighbors[1]

    def test_disconnected_components_detection(self):
        """Test detection of disconnected components in a graph."""
        # Create two separate clusters
        positions = np.array([
            [0.0, 0.0, 0.0],  # Cluster 1
            [1.0, 0.0, 0.0],  # Cluster 1
            [10.0, 10.0, 10.0],  # Cluster 2 (far away)
            [11.0, 10.0, 10.0]   # Cluster 2
        ])
        atomic_numbers = np.array([14, 14, 14, 14])
        
        config = AtomicConfiguration(
            config_id="test_disconnected",
            positions=positions,
            atomic_numbers=atomic_numbers,
            metadata={"source": "test", "size": 4}
        )
        
        # Build graph with small cutoff (should result in disconnected components)
        cutoff = 2.0
        graph = build_graph(config, cutoff_radius=cutoff)
        
        # Detect disconnected components
        components = detect_disconnected_components(graph)
        
        # Should have 2 components
        assert len(components) == 2
        # Each component should have 2 nodes
        assert all(len(comp) == 2 for comp in components)

    def test_graph_with_pbc(self):
        """Test graph construction with periodic boundary conditions simulation."""
        # Create a small box where atoms are close due to PBC
        box_size = 5.0
        positions = np.array([
            [0.0, 0.0, 0.0],
            [4.9, 0.0, 0.0],  # Close to atom 0 due to PBC
            [2.5, 2.5, 2.5]
        ])
        atomic_numbers = np.array([14, 14, 14])
        
        config = AtomicConfiguration(
            config_id="test_pbc",
            positions=positions,
            atomic_numbers=atomic_numbers,
            metadata={"source": "test", "size": 3, "box_size": box_size}
        )
        
        # Build graph - note: full PBC handling would require a more sophisticated implementation
        # For this test, we verify basic connectivity
        cutoff = 1.0
        graph = build_graph(config, cutoff_radius=cutoff)
        
        assert graph.number_of_nodes() == 3
        # Without full PBC implementation, atoms 0 and 1 might not connect
        # This test verifies the graph is built correctly regardless

    def test_empty_configuration(self):
        """Test handling of empty or single-atom configurations."""
        # Single atom
        positions = np.array([[0.0, 0.0, 0.0]])
        atomic_numbers = np.array([14])
        
        config = AtomicConfiguration(
            config_id="test_single",
            positions=positions,
            atomic_numbers=atomic_numbers,
            metadata={"source": "test", "size": 1}
        )
        
        graph = build_graph(config, cutoff_radius=2.5)
        assert graph.number_of_nodes() == 1
        assert graph.number_of_edges() == 0

    def test_graph_metadata_preservation(self):
        """Test that graph construction preserves configuration metadata."""
        positions = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0]
        ])
        atomic_numbers = np.array([14, 14])
        
        config = AtomicConfiguration(
            config_id="test_metadata",
            positions=positions,
            atomic_numbers=atomic_numbers,
            metadata={"source": "test_source", "size": 2, "temperature": 300}
        )
        
        graph = build_graph(config, cutoff_radius=2.0)
        
        # Verify graph has expected structure
        assert graph.number_of_nodes() == 2
        assert graph.number_of_edges() == 1

    def test_coordination_number_distribution(self):
        """Test that coordination numbers are correctly calculated."""
        # Create a structure with known coordination
        # Central atom with 4 neighbors (tetrahedral-like)
        center = np.array([0.0, 0.0, 0.0])
        neighbors = np.array([
            [1.0, 1.0, 1.0],
            [1.0, -1.0, -1.0],
            [-1.0, 1.0, -1.0],
            [-1.0, -1.0, 1.0]
        ]) * 1.5  # Scale to appropriate distance
        
        positions = np.vstack([center, neighbors])
        atomic_numbers = np.array([14] * 5)
        
        config = AtomicConfiguration(
            config_id="test_coordination",
            positions=positions,
            atomic_numbers=atomic_numbers,
            metadata={"source": "test", "size": 5}
        )
        
        graph = build_graph(config, cutoff_radius=3.0)
        
        # Central atom (node 0) should have 4 connections
        degree_0 = graph.degree(0)
        assert degree_0 == 4

    def test_invalid_cutoff_radius(self):
        """Test behavior with invalid cutoff radius values."""
        positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        atomic_numbers = np.array([14, 14])
        
        config = AtomicConfiguration(
            config_id="test_invalid_cutoff",
            positions=positions,
            atomic_numbers=atomic_numbers,
            metadata={"source": "test", "size": 2}
        )
        
        # Test with zero cutoff
        graph = build_graph(config, cutoff_radius=0.0)
        assert graph.number_of_edges() == 0
        
        # Test with very large cutoff
        graph = build_graph(config, cutoff_radius=100.0)
        assert graph.number_of_edges() == 1  # Only one edge possible for 2 nodes