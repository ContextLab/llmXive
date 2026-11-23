"""
Unit tests for clustering coefficient and LCC fraction calculation.
Tests US2 requirements for metrics calculation.
"""
import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import sys

# Add the project root to the path to allow imports
# Note: In a real execution environment, this would be handled by the runner
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.metrics.clustering import calculate_clustering_coefficients
from src.metrics.paths_and_lcc import calculate_lcc_and_path_length


class TestClusteringCoefficient:
    """Tests for global and local clustering coefficients."""

    def test_complete_graph_clustering(self):
        """In a complete graph, clustering coefficient should be 1.0."""
        # Complete graph K5
        G = nx.complete_graph(5)
        local, global_coef = calculate_clustering_coefficients(G)
        
        assert global_coef == pytest.approx(1.0)
        # All nodes in complete graph should have local clustering 1.0
        for node, coef in local.items():
            assert coef == pytest.approx(1.0)

    def test_path_graph_clustering(self):
        """In a path graph, clustering coefficient should be 0.0."""
        # Path graph P5
        G = nx.path_graph(5)
        local, global_coef = calculate_clustering_coefficients(G)
        
        assert global_coef == pytest.approx(0.0)
        # Internal nodes in path graph have 0 clustering (no triangles)
        # End nodes also have 0 (degree 1)

    def test_star_graph_clustering(self):
        """Star graph has 0 clustering (no triangles)."""
        # Star graph with 1 center and 5 leaves
        G = nx.star_graph(5)
        local, global_coef = calculate_clustering_coefficients(G)
        
        assert global_coef == pytest.approx(0.0)

    def test_random_graph_clustering(self):
        """Random graph should have non-trivial clustering."""
        # Erdos-Renyi graph
        G = nx.erdos_renyi_graph(20, 0.3, seed=42)
        local, global_coef = calculate_clustering_coefficients(G)
        
        assert 0.0 <= global_coef <= 1.0
        assert len(local) == G.number_of_nodes()

    def test_empty_graph_clustering(self):
        """Empty graph should return 0.0 for clustering."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3])
        local, global_coef = calculate_clustering_coefficients(G)
        
        # No edges means no triangles, clustering is 0
        assert global_coef == pytest.approx(0.0)
        assert all(c == 0.0 for c in local.values())

    def test_single_node_clustering(self):
        """Single node graph should return 0.0 for clustering."""
        G = nx.Graph()
        G.add_node(1)
        local, global_coef = calculate_clustering_coefficients(G)
        
        assert global_coef == pytest.approx(0.0)


class TestLCCFraction:
    """Tests for Largest Connected Component fraction and path length."""

    def test_connected_graph_lcc(self):
        """Connected graph should have LCC fraction = 1.0."""
        G = nx.complete_graph(10)
        lcc_fraction, is_connected, avg_path_length = calculate_lcc_and_path_length(G)
        
        assert lcc_fraction == pytest.approx(1.0)
        assert is_connected is True
        # Average path length in complete graph is 1.0
        assert avg_path_length == pytest.approx(1.0)

    def test_disconnected_graph_lcc(self):
        """Disconnected graph should have LCC fraction < 1.0."""
        # Two separate triangles
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])
        G.add_edges_from([(4, 5), (5, 6), (6, 4)])
        
        lcc_fraction, is_connected, avg_path_length = calculate_lcc_and_path_length(G)
        
        assert lcc_fraction == pytest.approx(0.5)  # 3 nodes in LCC out of 6
        assert is_connected is False
        # Path length should be calculated on LCC only
        assert avg_path_length == pytest.approx(1.0)  # LCC is a triangle

    def test_single_component_lcc(self):
        """Single node graph should have LCC fraction = 1.0."""
        G = nx.Graph()
        G.add_node(1)
        
        lcc_fraction, is_connected, avg_path_length = calculate_lcc_and_path_length(G)
        
        assert lcc_fraction == pytest.approx(1.0)
        assert is_connected is True
        # Path length for single node is 0.0
        assert avg_path_length == pytest.approx(0.0)

    def test_empty_graph_lcc(self):
        """Empty graph (no nodes) should handle gracefully."""
        G = nx.Graph()
        
        lcc_fraction, is_connected, avg_path_length = calculate_lcc_and_path_length(G)
        
        # Empty graph: LCC fraction is 0, not connected, path length is NaN
        assert lcc_fraction == pytest.approx(0.0)
        assert is_connected is False
        assert np.isnan(avg_path_length)

    def test_path_graph_lcc(self):
        """Path graph is connected, LCC fraction = 1.0."""
        G = nx.path_graph(10)
        
        lcc_fraction, is_connected, avg_path_length = calculate_lcc_and_path_length(G)
        
        assert lcc_fraction == pytest.approx(1.0)
        assert is_connected is True
        # Average path length in path graph P10 is (n-1)/3 * (n+1)/n approx
        # Exact: sum of all distances / (n*(n-1)/2)
        assert 0.0 < avg_path_length < 10.0

    def test_star_graph_lcc(self):
        """Star graph is connected, LCC fraction = 1.0."""
        G = nx.star_graph(10)
        
        lcc_fraction, is_connected, avg_path_length = calculate_lcc_and_path_length(G)
        
        assert lcc_fraction == pytest.approx(1.0)
        assert is_connected is True
        # Path length in star graph: center to leaf is 1, leaf to leaf is 2
        assert avg_path_length > 0.0

    def test_multiple_components_lcc(self):
        """Graph with multiple components of different sizes."""
        G = nx.Graph()
        # Component 1: 5 nodes (complete)
        G.add_edges_from([(i, j) for i in range(5) for j in range(i+1, 5)])
        # Component 2: 3 nodes (complete)
        G.add_edges_from([(i+5, j+5) for i in range(3) for j in range(i+1, 3)])
        # Component 3: 2 nodes (single edge)
        G.add_edge(8, 9)
        
        lcc_fraction, is_connected, avg_path_length = calculate_lcc_and_path_length(G)
        
        assert is_connected is False
        assert lcc_fraction == pytest.approx(5/10)  # 5 nodes in LCC out of 10
        # Path length should be 1.0 (complete graph K5)
        assert avg_path_length == pytest.approx(1.0)


class TestIntegration:
    """Integration tests combining clustering and LCC metrics."""

    def test_synthetic_defect_graph(self):
        """Test with a synthetic graph resembling defect distribution."""
        # Create a graph that mimics random defect distribution
        np.random.seed(42)
        num_nodes = 50
        # Random geometric graph (similar to threshold-based defect graph)
        G = nx.random_geometric_graph(num_nodes, radius=0.2, dim=2, seed=42)
        
        # Calculate clustering
        local_cluster, global_cluster = calculate_clustering_coefficients(G)
        
        # Calculate LCC metrics
        lcc_frac, is_conn, avg_path = calculate_lcc_and_path_length(G)
        
        # Assertions
        assert 0.0 <= global_cluster <= 1.0
        assert len(local_cluster) == G.number_of_nodes()
        assert 0.0 <= lcc_frac <= 1.0
        assert isinstance(is_conn, bool)
        
        # If connected, avg_path should be finite
        if is_conn:
            assert not np.isnan(avg_path)
            assert avg_path >= 0.0

    def test_grid_graph_properties(self):
        """Test with a grid graph (lattice-like structure)."""
        G = nx.grid_2d_graph(5, 5)
        
        local, global_coef = calculate_clustering_coefficients(G)
        lcc_frac, is_conn, avg_path = calculate_lcc_and_path_length(G)
        
        # Grid graphs have non-zero clustering (squares have no diagonals, so 0)
        # Actually, grid graphs have 0 clustering because no triangles
        assert global_coef == pytest.approx(0.0)
        
        # Grid is connected
        assert is_conn is True
        assert lcc_frac == pytest.approx(1.0)
        
        # Path length should be finite and positive
        assert not np.isnan(avg_path)
        assert avg_path > 0.0