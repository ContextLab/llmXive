"""
Unit tests for persistence_utils module.
"""
import pytest
import networkx as nx
import numpy as np
from code.utils.persistence_utils import (
    compute_shortest_path_matrix,
    build_shortest_path_filtration,
    compute_persistence_diagram,
    handle_empty_diagram,
    compute_betti_numbers,
    get_topological_features
)

class TestShortestPathMatrix:
    def test_simple_graph(self):
        """Test shortest path computation on a simple graph."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        dist_matrix = compute_shortest_path_matrix(graph)
        
        assert dist_matrix.shape == (4, 4)
        assert dist_matrix[0, 3] == 3.0
        assert dist_matrix[0, 1] == 1.0
        assert np.diag(dist_matrix).sum() == 0.0  # Diagonal should be 0

    def test_empty_graph(self):
        """Test shortest path on empty graph."""
        graph = nx.Graph()
        dist_matrix = compute_shortest_path_matrix(graph)
        
        assert dist_matrix.size == 0
        assert dist_matrix.shape == (0, 0)

    def test_disconnected_graph(self):
        """Test shortest path on disconnected graph."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (2, 3)])
        
        dist_matrix = compute_shortest_path_matrix(graph)
        
        assert dist_matrix.shape == (4, 4)
        assert np.isinf(dist_matrix[0, 2])  # Unreachable
        assert dist_matrix[0, 1] == 1.0

class TestShortestPathFiltration:
    def test_simple_graph(self):
        """Test filtration building on a simple graph."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        simplices, vertices = build_shortest_path_filtration(graph)
        
        assert len(vertices) == 4
        assert len(simplices) > 0
        
        # Check that vertices have filtration value 0
        for v in vertices:
            assert v[1] == 0.0
        
        # Check that simplices are sorted by value
        values = [s[2] for s in simplices]
        assert values == sorted(values)

    def test_empty_graph(self):
        """Test filtration on empty graph."""
        graph = nx.Graph()
        simplices, vertices = build_shortest_path_filtration(graph)
        
        assert len(simplices) == 0
        assert len(vertices) == 0

class TestPersistenceDiagram:
    def test_simple_cycle(self):
        """Test persistence diagram on a simple cycle."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 0)])  # Triangle
        
        diagram = compute_persistence_diagram(graph)
        
        # Should have at least one 0-dimensional feature
        assert len(diagram) > 0
        
        # Check that all features have non-negative persistence
        for birth, death in diagram:
            assert death >= birth

    def test_empty_graph(self):
        """Test persistence diagram on empty graph."""
        graph = nx.Graph()
        diagram = compute_persistence_diagram(graph)
        
        assert diagram == []

    def test_disconnected_graph(self):
        """Test persistence diagram on disconnected graph."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (2, 3)])
        
        diagram = compute_persistence_diagram(graph)
        
        # Should handle disconnected graphs gracefully
        # May return empty or default features depending on implementation
        assert isinstance(diagram, list)

class TestEmptyDiagramHandling:
    def test_non_empty_diagram(self):
        """Test that non-empty diagrams are returned unchanged."""
        diagram = [(0.0, 1.0), (0.5, 2.0)]
        result = handle_empty_diagram(diagram)
        
        assert result == diagram

    def test_empty_diagram(self):
        """Test that empty diagrams get default features."""
        diagram = []
        result = handle_empty_diagram(diagram, default_value=0.5)
        
        assert len(result) == 1
        assert result[0][0] == 0.0
        assert result[0][1] == 0.5

    def test_custom_default_value(self):
        """Test custom default value handling."""
        diagram = []
        result = handle_empty_diagram(diagram, default_value=10.0)
        
        assert result[0][1] == 10.0

class TestBettiNumbers:
    def test_simple_graph(self):
        """Test Betti number computation."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        betti = compute_betti_numbers(graph, threshold=2.0)
        
        assert betti[0] == 1  # One connected component
        assert betti[1] == 0  # No cycles

    def test_cycle_graph(self):
        """Test Betti numbers on a cycle."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 0)])  # Triangle
        
        betti = compute_betti_numbers(graph, threshold=2.0)
        
        assert betti[0] == 1  # One connected component
        assert betti[1] >= 1  # At least one cycle

    def test_empty_graph(self):
        """Test Betti numbers on empty graph."""
        graph = nx.Graph()
        betti = compute_betti_numbers(graph, threshold=1.0)
        
        assert betti[0] == 0
        assert betti[1] == 0

class TestTopologicalFeatures:
    def test_full_feature_extraction(self):
        """Test complete feature extraction."""
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])
        
        features = get_topological_features(graph)
        
        assert 'persistence_diagram' in features
        assert 'num_features' in features
        assert 'persistence_sum' in features
        assert 'max_persistence' in features
        assert 'betti_0_at_threshold' in features
        assert 'betti_1_at_threshold' in features
        
        assert features['num_features'] >= 0
        assert features['persistence_sum'] >= 0
        assert features['max_persistence'] >= 0

    def test_empty_graph_features(self):
        """Test feature extraction on empty graph."""
        graph = nx.Graph()
        features = get_topological_features(graph)
        
        assert features['num_features'] == 0
        assert features['persistence_sum'] == 0.0
        assert features['max_persistence'] == 0.0

    def test_empty_handling_disabled(self):
        """Test feature extraction with empty handling disabled."""
        graph = nx.Graph()
        features = get_topological_features(graph, use_empty_handling=False)
        
        assert features['persistence_diagram'] == []
        assert features['num_features'] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])