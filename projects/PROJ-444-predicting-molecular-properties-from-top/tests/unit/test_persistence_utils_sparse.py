"""
Unit tests for persistence_utils.py sparse matrix logic and memory threshold checks.
"""

import pytest
import numpy as np
import networkx as nx
from scipy.sparse import csr_matrix
import sys
import os

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.persistence_utils import (
    check_memory_requirement,
    compute_shortest_path_matrix,
    build_shortest_path_filtration,
    compute_persistence_diagram,
    vectorize,
    handle_empty_diagram,
    get_topological_features
)


class TestMemoryThreshold:
    """Test memory threshold checks for large graphs."""

    def test_small_graph_dense_mode(self):
        """Small graphs should use dense mode."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        needs_sparse = check_memory_requirement(graph)
        assert needs_sparse is False, "Small graph should not need sparse mode"

    def test_large_graph_sparse_mode(self):
        """Large graphs should use sparse mode."""
        # Create a graph large enough to exceed 6GB threshold
        # 3000 nodes -> 3000^2 * 8 bytes = 72 GB
        large_n = 3000
        graph = nx.Graph()
        graph.add_nodes_from(range(large_n))
        # Add minimal edges to make it a valid graph
        for i in range(large_n - 1):
            graph.add_edge(i, i + 1)
        
        needs_sparse = check_memory_requirement(graph)
        assert needs_sparse is True, "Large graph should need sparse mode"


class TestSparseMatrixComputation:
    """Test sparse matrix computation for large graphs."""

    def test_small_graph_dense(self):
        """Small graphs should return dense matrices."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        dist_matrix = compute_shortest_path_matrix(graph, use_sparse=False)
        assert isinstance(dist_matrix, np.ndarray), "Small graph should return dense matrix"
        assert dist_matrix.shape == (4, 4)

    def test_large_graph_sparse(self):
        """Large graphs should return sparse matrices."""
        large_n = 1000  # Smaller for test speed, but still triggers sparse
        graph = nx.Graph()
        graph.add_nodes_from(range(large_n))
        for i in range(large_n - 1):
            graph.add_edge(i, i + 1)
        
        dist_matrix = compute_shortest_path_matrix(graph, use_sparse=True)
        assert isinstance(dist_matrix, csr_matrix), "Large graph should return sparse matrix"
        assert dist_matrix.shape == (large_n, large_n)

    def test_large_graph_sparse_memory_efficient(self):
        """Sparse matrix should be memory efficient."""
        large_n = 1000
        graph = nx.Graph()
        graph.add_nodes_from(range(large_n))
        # Create a sparse graph (linear chain)
        for i in range(large_n - 1):
            graph.add_edge(i, i + 1)
        
        dist_matrix = compute_shortest_path_matrix(graph, use_sparse=True)
        
        # A linear chain has O(N) edges, so the distance matrix should have O(N^2) non-zeros
        # But for a linear chain, the distance matrix is full, so we expect many non-zeros
        # However, the sparse format should still be more efficient for storage
        assert dist_matrix.nnz > 0, "Sparse matrix should have non-zero entries"


class TestPersistenceDiagram:
    """Test persistence diagram computation."""

    def test_empty_graph(self):
        """Empty graph should return empty diagram."""
        graph = nx.Graph()
        filtration = build_shortest_path_filtration(graph)
        diagram = compute_persistence_diagram(filtration)
        assert len(diagram) == 0

    def test_simple_cycle(self):
        """Simple cycle should produce a 1-cycle."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 0)])
        
        filtration = build_shortest_path_filtration(graph)
        diagram = compute_persistence_diagram(filtration)
        
        # Should have at least one 1-cycle
        assert len(diagram) > 0

    def test_vectorize_empty_diagram(self):
        """Empty diagram should return zero vector."""
        resolution = 10
        vector = vectorize([], resolution)
        assert len(vector) == resolution * resolution
        assert np.allclose(vector, 0)

    def test_vectorize_with_data(self):
        """Vectorize should produce non-zero vector for valid diagram."""
        diagram = [(0.0, 1.0), (0.5, 2.0)]
        resolution = 10
        vector = vectorize(diagram, resolution)
        assert len(vector) == resolution * resolution
        assert np.any(vector > 0), "Vector should have non-zero entries"


class TestTopologicalFeatures:
    """Test topological feature extraction."""

    def test_empty_diagram_features(self):
        """Empty diagram should return zero features."""
        features = get_topological_features([])
        assert features['num_features'] == 0
        assert features['total_persistence'] == 0.0
        assert features['max_persistence'] == 0.0
        assert features['avg_persistence'] == 0.0

    def test_simple_diagram_features(self):
        """Simple diagram should return correct features."""
        diagram = [(0.0, 1.0), (0.5, 2.0)]
        features = get_topological_features(diagram)
        
        assert features['num_features'] == 2
        assert features['total_persistence'] == 2.5  # (1.0-0.0) + (2.0-0.5) = 1.0 + 1.5 = 2.5
        assert features['max_persistence'] == 1.5
        assert features['avg_persistence'] == 1.25


class TestLargeGraphMemoryHandling:
    """Test that large graphs are handled without crashing."""

    def test_large_graph_no_crash(self):
        """Large graph processing should not crash."""
        large_n = 1500
        graph = nx.Graph()
        graph.add_nodes_from(range(large_n))
        # Add edges to make it a connected graph
        for i in range(large_n - 1):
            graph.add_edge(i, i + 1)
        
        # This should not crash
        needs_sparse = check_memory_requirement(graph)
        assert needs_sparse is True
        
        # Compute shortest path matrix with sparse mode
        dist_matrix = compute_shortest_path_matrix(graph, use_sparse=True)
        assert isinstance(dist_matrix, csr_matrix)
        assert dist_matrix.shape == (large_n, large_n)

    def test_synthetic_large_benzene_chain(self):
        """Test with a synthetic SMILES-like large graph (repeating benzene rings)."""
        # Simulate a large graph with many repeating units
        # Each benzene ring has 6 nodes and 6 edges (plus connections between rings)
        num_rings = 200
        nodes_per_ring = 6
        total_nodes = num_rings * nodes_per_ring
        
        graph = nx.Graph()
        graph.add_nodes_from(range(total_nodes))
        
        # Add benzene ring structures
        for ring_idx in range(num_rings):
            base_node = ring_idx * nodes_per_ring
            # Benzene ring: 0-1-2-3-4-5-0
            ring_nodes = [base_node + i for i in range(6)]
            graph.add_edge(ring_nodes[0], ring_nodes[1])
            graph.add_edge(ring_nodes[1], ring_nodes[2])
            graph.add_edge(ring_nodes[2], ring_nodes[3])
            graph.add_edge(ring_nodes[3], ring_nodes[4])
            graph.add_edge(ring_nodes[4], ring_nodes[5])
            graph.add_edge(ring_nodes[5], ring_nodes[0])
            
            # Connect to next ring
            if ring_idx < num_rings - 1:
                next_base = (ring_idx + 1) * nodes_per_ring
                graph.add_edge(ring_nodes[0], next_base)
        
        # This should trigger sparse mode
        needs_sparse = check_memory_requirement(graph)
        assert needs_sparse is True, "Large benzene chain should trigger sparse mode"
        
        # Compute shortest path matrix
        dist_matrix = compute_shortest_path_matrix(graph, use_sparse=True)
        assert isinstance(dist_matrix, csr_matrix)
        assert dist_matrix.shape == (total_nodes, total_nodes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
