import pytest
import networkx as nx
import numpy as np
from code.descriptors import (
    calculate_ring_statistics,
    calculate_steinhardt_q6,
    calculate_clustering_coefficient,
    calculate_descriptors,
    extract_ring_features
)
from code.models.atomic_config import AtomicConfiguration

class TestCalculateRingStatistics:
    def test_empty_graph(self):
        G = nx.Graph()
        result = calculate_ring_statistics(G)
        assert all(v == 0 for v in result.values())
        assert len(result) == 8 # 3 to 10

    def test_simple_ring(self):
        # Create a simple triangle (3-ring)
        G = nx.cycle_graph(3)
        result = calculate_ring_statistics(G)
        assert result[3] == 1
        assert result[4] == 0

    def test_square_ring(self):
        G = nx.cycle_graph(4)
        result = calculate_ring_statistics(G)
        assert result[4] == 1
        assert result[3] == 0

    def test_bonded_rings(self):
        # Two triangles sharing an edge (diamond shape with a cross)
        # Nodes 0-1-2-0 and 1-2-3-1
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0), (1, 3), (2, 3)])
        result = calculate_ring_statistics(G)
        # Should find two 3-rings
        assert result[3] == 2

class TestCalculateSteinhardtQ6:
    def test_simple_crystal_lattice(self):
        # Create a small FCC-like cluster (approximate)
        # Just a few points to test calculation doesn't crash
        coords = np.array([
            [0, 0, 0],
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 1]
        ], dtype=float)
        
        config = AtomicConfiguration(
            atomic_numbers=[14, 14, 14, 14],
            coordinates=coords
        )
        
        q6 = calculate_steinhardt_q6(config)
        assert 0.0 <= q6 <= 1.0

    def test_random_positions(self):
        np.random.seed(42)
        coords = np.random.rand(10, 3) * 5.0
        config = AtomicConfiguration(
            atomic_numbers=[14] * 10,
            coordinates=coords
        )
        q6 = calculate_steinhardt_q6(config)
        assert 0.0 <= q6 <= 1.0

    def test_single_atom(self):
        coords = np.array([[0, 0, 0]], dtype=float)
        config = AtomicConfiguration(
            atomic_numbers=[14],
            coordinates=coords
        )
        q6 = calculate_steinhardt_q6(config)
        assert q6 == 0.0

class TestCalculateClusteringCoefficient:
    def test_empty_graph(self):
        G = nx.Graph()
        assert calculate_clustering_coefficient(G) == 0.0

    def test_triangle(self):
        G = nx.cycle_graph(3)
        # A triangle has clustering coefficient 1.0 for all nodes
        assert calculate_clustering_coefficient(G) == 1.0

    def test_path_graph(self):
        G = nx.path_graph(3)
        # 0-1-2. Node 1 has neighbors 0,2. No edge 0-2. CC=0.
        # Nodes 0 and 2 have degree 1, CC=0 by definition.
        assert calculate_clustering_coefficient(G) == 0.0

class TestCalculateDescriptors:
    def test_full_pipeline(self):
        # Create a simple graph and config
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0), (0, 3), (3, 4)])
        
        coords = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [0.5, 0.866, 0],
            [0.5, 0.288, 0.816],
            [1.5, 0.288, 0.816]
        ], dtype=float)
        
        config = AtomicConfiguration(
            atomic_numbers=[14] * 5,
            coordinates=coords
        )
        
        descriptors = calculate_descriptors(config, G)
        
        assert "ring_statistics" in descriptors
        assert "steinhardt_q6" in descriptors
        assert "clustering_coefficient" in descriptors
        
        assert isinstance(descriptors["ring_statistics"], dict)
        assert isinstance(descriptors["steinhardt_q6"], float)
        assert isinstance(descriptors["clustering_coefficient"], float)

class TestExtractRingFeatures:
    def test_flatten(self):
        stats = {3: 2, 4: 1, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0}
        features = extract_ring_features(stats)
        assert len(features) == 8
        assert features[0] == 2 # size 3
        assert features[1] == 1 # size 4
        assert features[2] == 0 # size 5