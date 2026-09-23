import pytest
import networkx as nx
import numpy as np
from code.graph_builder import (
    build_coupling_graph,
    compute_shortest_path_metrics,
    compute_clustering_and_assortativity,
    compute_edge_betweenness_and_spectral_gap,
    process_device_coupling_map
)

class TestDisconnectedGraphHandling:
    """Tests specifically for disconnected graph handling per T024."""

    def test_spectral_gap_zero_for_disconnected(self):
        """Verify spectral gap is set to 0 for disconnected graphs."""
        # Create a graph with two disconnected components
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])  # Two separate edges
        
        result = compute_edge_betweenness_and_spectral_gap(G)
        
        assert result["spectral_gap"] == 0.0, "Spectral gap must be 0 for disconnected graphs"

    def test_path_metrics_on_largest_component(self):
        """Verify path metrics are computed only on the largest connected component."""
        # Graph: 0-1-2 (size 3) and 3-4 (size 2)
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (3, 4)])
        
        result = compute_shortest_path_metrics(G)
        
        # Largest component is 0-1-2
        # Avg shortest path for 0-1-2: (1+2+1+1+2+1)/6 = 8/6 = 1.333...
        # Diameter is 2 (0 to 2)
        expected_avg = 4.0 / 3.0  # 1.333...
        expected_diameter = 2
        
        assert abs(result["avg_shortest_path"] - expected_avg) < 1e-6
        assert result["diameter"] == expected_diameter

    def test_disconnected_graph_detection(self):
        """Verify process_device_coupling_map correctly identifies disconnected graphs."""
        # Two separate components: 0-1 and 2-3
        coupling_map = [(0, 1), (2, 3)]
        num_qubits = 4
        
        result = process_device_coupling_map("test", coupling_map, num_qubits)
        
        assert result["is_connected"] is False

    def test_connected_graph_spectral_gap_nonzero(self):
        """Verify connected graph has non-zero spectral gap (unless trivial)."""
        # Simple line: 0-1-2-3
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        result = compute_edge_betweenness_and_spectral_gap(G)
        
        # For a line graph with 4 nodes, spectral gap > 0
        assert result["spectral_gap"] > 0.0

class TestGraphBuilderBasics:
    """Basic tests for graph builder functionality."""

    def test_build_coupling_graph_undirected(self):
        """Verify coupling map is treated as undirected."""
        coupling_map = [(0, 1), (1, 2)]
        G = build_coupling_graph(coupling_map, 3)
        
        assert G.has_edge(0, 1)
        assert G.has_edge(1, 0)  # Undirected
        assert G.has_edge(1, 2)
        assert G.has_edge(2, 1)
        assert len(G.edges()) == 2

    def test_build_coupling_graph_includes_isolated_qubits(self):
        """Verify isolated qubits are included in the graph."""
        coupling_map = [(0, 1)]
        G = build_coupling_graph(coupling_map, 4)  # 4 qubits, but only 2 connected
        
        assert len(G.nodes()) == 4
        assert 2 in G.nodes()
        assert 3 in G.nodes()
        assert not G.has_edge(0, 2)

    def test_compute_shortest_path_empty_graph(self):
        """Verify handling of graph with no edges."""
        G = nx.Graph()
        G.add_nodes_from(range(3))
        
        result = compute_shortest_path_metrics(G)
        
        assert result["avg_shortest_path"] == 0.0
        assert result["diameter"] == 0.0

    def test_compute_clustering_coefficient(self):
        """Verify clustering coefficient calculation."""
        # Triangle: 0-1-2-0
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])
        
        result = compute_clustering_and_assortativity(G)
        
        # Complete graph K3 has clustering coefficient 1.0
        assert result["clustering_coeff"] == 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
