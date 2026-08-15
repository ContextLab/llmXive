import pytest
import networkx as nx
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.graph_builder import (
    build_coupling_graph,
    compute_shortest_path_metrics,
    compute_clustering_and_assortativity,
    compute_edge_betweenness_and_spectral_gap,
    process_device_coupling_map
)

class TestBuildCouplingGraph:
    def test_empty_map(self):
        G = build_coupling_graph([])
        assert G.number_of_nodes() == 0
        assert G.number_of_edges() == 0

    def test_simple_line(self):
        # 0 -- 1 -- 2
        coupling_map = [(0, 1), (1, 2)]
        G = build_coupling_graph(coupling_map)
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 2
        assert nx.is_connected(G)

    def test_ring(self):
        # 0 -- 1
        # |    |
        # 3 -- 2
        coupling_map = [(0, 1), (1, 2), (2, 3), (3, 0)]
        G = build_coupling_graph(coupling_map)
        assert G.number_of_nodes() == 4
        assert G.number_of_edges() == 4
        assert nx.is_connected(G)
        # Clustering should be 0 for a pure ring without chords
        assert nx.average_clustering(G) == 0.0

    def test_directed_to_undirected(self):
        # Even if input is directed (0->1, 1->0), graph should be undirected
        coupling_map = [(0, 1), (1, 0)]
        G = build_coupling_graph(coupling_map)
        # Should result in a single edge
        assert G.number_of_edges() == 1
        assert G.has_edge(0, 1)

class TestShortestPathMetrics:
    def test_empty_graph(self):
        G = nx.Graph()
        metrics = compute_shortest_path_metrics(G)
        assert metrics['avg_shortest_path'] != metrics['avg_shortest_path'] # NaN check
        assert metrics['diameter'] != metrics['diameter']

    def test_connected_line(self):
        # 0-1-2-3
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])
        metrics = compute_shortest_path_metrics(G)
        # Avg path length for line of 4:
        # Pairs: (0,1)=1, (0,2)=2, (0,3)=3, (1,2)=1, (1,3)=2, (2,3)=1
        # Sum = 10, Count = 6, Avg = 1.666...
        assert abs(metrics['avg_shortest_path'] - 1.6666666666666667) < 1e-6
        assert metrics['diameter'] == 3

    def test_disconnected_graph(self):
        # Two separate components: 0-1 and 2-3
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])
        metrics = compute_shortest_path_metrics(G)
        # Should compute on largest component (size 2)
        # Component 0-1: avg path = 1, diam = 1
        assert metrics['avg_shortest_path'] == 1.0
        assert metrics['diameter'] == 1.0

class TestClusteringAssortativity:
    def test_empty_graph(self):
        G = nx.Graph()
        metrics = compute_clustering_and_assortativity(G)
        assert metrics['clustering_coeff'] != metrics['clustering_coeff']
        assert metrics['assortativity'] != metrics['assortativity']

    def test_triangle(self):
        # 0-1-2-0 (clique)
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])
        metrics = compute_clustering_and_assortativity(G)
        assert metrics['clustering_coeff'] == 1.0
        # Assortativity for a complete graph is 0 (or undefined depending on implementation, but usually 0)
        # Actually for K3, degree is 2 for all, so correlation is undefined/0
        # NetworkX returns 0.0 for regular graphs
        assert metrics['assortativity'] == 0.0

class TestSpectralGap:
    def test_empty_graph(self):
        G = nx.Graph()
        metrics = compute_edge_betweenness_and_spectral_gap(G)
        assert metrics['spectral_gap'] != metrics['spectral_gap']

    def test_single_edge(self):
        # 0 -- 1
        G = nx.Graph()
        G.add_edge(0, 1)
        metrics = compute_edge_betweenness_and_spectral_gap(G)
        # Laplacian of K2: [[1, -1], [-1, 1]]
        # Eigenvalues: 0, 2. Gap = 2.
        assert abs(metrics['spectral_gap'] - 2.0) < 1e-6
        # Edge betweenness for single edge is 1.0
        assert metrics['edge_betweenness_mean'] == 1.0

class TestProcessDeviceCouplingMap:
    def test_full_pipeline(self):
        coupling_map = [(0, 1), (1, 2), (2, 3)]
        result = process_device_coupling_map("test_device", coupling_map)
        
        assert result['device_id'] == "test_device"
        assert result['num_nodes'] == 4
        assert result['num_edges'] == 3
        assert 'avg_shortest_path' in result
        assert 'diameter' in result
        assert 'clustering_coeff' in result
        assert 'assortativity' in result
        assert 'spectral_gap' in result
        assert 'edge_betweenness_mean' in result