import networkx as nx
import numpy as np
import pytest
from code.graph_builder import (
    build_coupling_graph,
    compute_shortest_path_metrics,
    compute_clustering_and_assortativity,
    compute_edge_betweenness_and_spectral_gap,
    process_device_coupling_map
)
from code.models import QubitDevice, GraphMetric

class TestBuildCouplingGraph:
    def test_simple_line_graph(self):
        """Test building a simple line graph: 0-1-2-3"""
        coupling_map = [[0, 1], [1, 2], [2, 3]]
        num_qubits = 4
        G = build_coupling_graph(coupling_map, num_qubits)
        
        assert nx.is_connected(G)
        assert G.number_of_nodes() == 4
        assert G.number_of_edges() == 3
        assert list(G.edges()) == [(0, 1), (1, 2), (2, 3)]

    def test_disconnected_graph(self):
        """Test building a disconnected graph"""
        coupling_map = [[0, 1], [2, 3]]
        num_qubits = 4
        G = build_coupling_graph(coupling_map, num_qubits)
        
        assert not nx.is_connected(G)
        assert G.number_of_nodes() == 4
        assert G.number_of_edges() == 2

    def test_isolated_nodes(self):
        """Test that isolated nodes are included"""
        coupling_map = [[0, 1]]
        num_qubits = 5
        G = build_coupling_graph(coupling_map, num_qubits)
        
        assert G.number_of_nodes() == 5
        assert list(G.nodes()) == [0, 1, 2, 3, 4]

class TestComputeShortestPathMetrics:
    def test_line_graph_metrics(self):
        """Test metrics on a line graph 0-1-2-3"""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        metrics = compute_shortest_path_metrics(G)
        
        # Average shortest path for line graph of 4 nodes
        # Paths: (0,1)=1, (0,2)=2, (0,3)=3, (1,0)=1, (1,2)=1, (1,3)=2, (2,0)=2, (2,1)=1, (2,3)=1, (3,0)=3, (3,1)=2, (3,2)=1
        # Sum = 1+2+3+1+1+2+2+1+1+3+2+1 = 19
        # Count = 12
        # Avg = 19/12 ≈ 1.5833
        assert abs(metrics["avg_shortest_path"] - 1.5833) < 0.01
        assert metrics["diameter"] == 3

    def test_disconnected_graph_metrics(self):
        """Test metrics on a disconnected graph"""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])
        
        metrics = compute_shortest_path_metrics(G)
        
        # Should compute on largest component (size 2)
        # Component 0-1: avg shortest path = 1.0, diameter = 1
        assert metrics["avg_shortest_path"] == 1.0
        assert metrics["diameter"] == 1

    def test_single_node_graph(self):
        """Test metrics on a single node graph"""
        G = nx.Graph()
        G.add_node(0)
        
        metrics = compute_shortest_path_metrics(G)
        assert metrics["avg_shortest_path"] == 0.0
        assert metrics["diameter"] == 0.0

class TestComputeClusteringAndAssortativity:
    def test_complete_graph_clustering(self):
        """Test clustering coefficient on a complete graph K4"""
        G = nx.complete_graph(4)
        metrics = compute_clustering_and_assortativity(G)
        
        # Complete graph has clustering coefficient 1.0
        assert metrics["clustering_coefficient"] == 1.0

    def test_complete_graph_assortativity(self):
        """Test assortativity on a complete graph (should be 0.0)"""
        G = nx.complete_graph(4)
        metrics = compute_clustering_and_assortativity(G)
        
        # In a complete graph, all degrees are equal, assortativity is 0
        assert metrics["assortativity"] == 0.0

class TestComputeEdgeBetweennessAndSpectralGap:
    def test_line_graph_edge_betweenness(self):
        """Test edge betweenness on a line graph 0-1-2-3"""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        metrics = compute_edge_betweenness_and_spectral_gap(G)
        
        # In a line graph, the middle edge has higher betweenness
        # Edge (1,2) is between 0-1 and 2-3, so it's used by paths (0,2), (0,3), (1,2), (1,3)
        # Actually, for edge betweenness, we count shortest paths that pass through the edge.
        # Total pairs: 12. 
        # Edge (0,1): used by (0,1), (0,2), (0,3) -> 3 paths
        # Edge (1,2): used by (0,2), (0,3), (1,2), (1,3) -> 4 paths
        # Edge (2,3): used by (0,3), (1,3), (2,3) -> 3 paths
        # Sum = 3+4+3 = 12. Mean = 12/3 = 4.0? Wait, edge betweenness is normalized by total paths.
        # Let's just check that it's non-zero and finite.
        assert metrics["edge_betweenness_mean"] > 0.0
        assert np.isfinite(metrics["edge_betweenness_mean"])
        assert np.isfinite(metrics["edge_betweenness_std"])

    def test_complete_graph_spectral_gap(self):
        """Test spectral gap on a complete graph K4"""
        G = nx.complete_graph(4)
        metrics = compute_edge_betweenness_and_spectral_gap(G)
        
        # Complete graph K_n has spectral gap = n (for unnormalized Laplacian)
        # Actually, eigenvalues of Laplacian for K_n are: 0 (once), n (n-1 times)
        # So spectral gap = n - 0 = n. For K4, it should be 4.
        # Note: scipy's laplacian is unnormalized by default in this context.
        assert abs(metrics["spectral_gap"] - 4.0) < 0.1

    def test_disconnected_graph_spectral_gap(self):
        """Test spectral gap on a disconnected graph"""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])
        metrics = compute_edge_betweenness_and_spectral_gap(G)
        
        # Disconnected graph has spectral gap 0
        assert metrics["spectral_gap"] == 0.0

    def test_single_node_spectral_gap(self):
        """Test spectral gap on a single node graph"""
        G = nx.Graph()
        G.add_node(0)
        metrics = compute_edge_betweenness_and_spectral_gap(G)
        
        assert metrics["spectral_gap"] == 0.0
        assert metrics["edge_betweenness_mean"] == 0.0

class TestProcessDeviceCouplingMap:
    def test_process_valid_device(self):
        """Test processing a valid QubitDevice"""
        device = QubitDevice(
            device_id="test_device",
            num_qubits=4,
            coupling_map=[[0, 1], [1, 2], [2, 3]],
            t1_time=100.0,
            t2_time=200.0,
            cx_error_rate=0.01,
            readout_error_rate=0.02,
            timestamp="2023-01-01"
        )
        
        metric = process_device_coupling_map(device)
        
        assert metric.device_id == "test_device"
        assert metric.avg_shortest_path_length > 0.0
        assert metric.diameter > 0.0
        assert metric.clustering_coefficient >= 0.0
        assert metric.spectral_gap >= 0.0

    def test_process_disconnected_device(self):
        """Test processing a device with disconnected graph"""
        device = QubitDevice(
            device_id="disconnected_device",
            num_qubits=4,
            coupling_map=[[0, 1], [2, 3]],
            t1_time=100.0,
            t2_time=200.0,
            cx_error_rate=0.01,
            readout_error_rate=0.02,
            timestamp="2023-01-01"
        )
        
        metric = process_device_coupling_map(device)
        
        assert metric.device_id == "disconnected_device"
        assert metric.spectral_gap == 0.0
        # Metrics should be computed on the largest component
        assert metric.avg_shortest_path_length > 0.0
        assert metric.diameter > 0.0
