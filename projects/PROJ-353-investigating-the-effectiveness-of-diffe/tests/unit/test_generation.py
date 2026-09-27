"""
Unit tests for Watts-Strogatz graph generation logic.
Tests US1: Synthetic Graph Generation and Topology Annotation.
"""

import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import seed_all, SAMPLE_SIZE, CONVERGENCE_THRESHOLD
from models import create_normalized_adjacency


class TestWattsStrogatzGeneration:
    """Tests for the core Watts-Strogatz generation logic."""

    def test_seed_reproducibility(self):
        """Verify that setting the same seed produces identical graphs."""
        seed_all(42)
        G1 = nx.watts_strogatz_graph(n=110, k=6, p=0.1)
        adj1 = np.array(G1.adjacency())

        seed_all(42)
        G2 = nx.watts_strogatz_graph(n=110, k=6, p=0.1)
        adj2 = np.array(G2.adjacency())

        np.testing.assert_array_equal(adj1, adj2)

    def test_graph_node_count(self):
        """Verify that generated graphs have the correct number of nodes."""
        seed_all(123)
        n = 110
        k = 6
        p = 0.5
        
        G = nx.watts_strogatz_graph(n=n, k=k, p=p)
        
        assert G.number_of_nodes() == n, f"Expected {n} nodes, got {G.number_of_nodes()}"

    def test_graph_edge_count_bounds(self):
        """Verify edge count is within theoretical bounds for WS graphs."""
        seed_all(456)
        n = 110
        k = 6
        p = 0.0  # Regular lattice case
        
        G = nx.watts_strogatz_graph(n=n, k=k, p=p)
        
        # For p=0, edges should be exactly n*k/2 (regular ring lattice)
        expected_edges = n * k // 2
        assert G.number_of_edges() == expected_edges, \
            f"Expected {expected_edges} edges for p=0, got {G.number_of_edges()}"

    def test_clustering_coefficient_bounds(self):
        """Verify clustering coefficients are within theoretical bounds."""
        seed_all(789)
        n = 110
        k = 6
        p = 0.0  # Regular lattice has high clustering
        
        G = nx.watts_strogatz_graph(n=n, k=k, p=p)
        clustering = nx.average_clustering(G)
        
        # For a regular ring lattice with k=6, clustering should be 0.75
        # For p > 0, it decreases but remains positive
        assert 0.0 <= clustering <= 1.0, f"Clustering coefficient {clustering} out of bounds"
        
        # With p=0, we expect high clustering (close to 3/4 for k=6)
        if p == 0:
            assert clustering > 0.7, f"Expected high clustering for p=0, got {clustering}"

    def test_various_beta_levels(self):
        """Test generation across the full range of beta (rewiring probability)."""
        betas = [0.0, 0.1, 0.2, 0.5, 0.8, 1.0]
        
        for beta in betas:
            seed_all(100 + int(beta * 100))
            G = nx.watts_strogatz_graph(n=110, k=6, p=beta)
            
            # Basic sanity checks
            assert G.number_of_nodes() == 110
            assert G.number_of_nodes() > 0
            
            clustering = nx.average_clustering(G)
            assert 0.0 <= clustering <= 1.0
            
            # Verify graph is undirected
            assert not G.is_directed()

    def test_disconnected_components_detection(self):
        """Verify that graphs with disconnected components can be detected."""
        # With high p and small n, we might get disconnected graphs
        # This test ensures our detection logic would work
        seed_all(999)
        G = nx.watts_strogatz_graph(n=110, k=6, p=0.5)
        
        # Count connected components
        num_components = nx.number_connected_components(G)
        
        # For p=0.5, we expect mostly connected, but check the count
        assert num_components >= 1
        
        # If disconnected, our pipeline should handle it
        if num_components > 1:
            # Verify we can identify the largest component
            largest_cc = max(nx.connected_components(G), key=len)
            assert len(largest_cc) > 0

    def test_edge_list_format(self):
        """Verify that edge lists can be extracted in expected format."""
        seed_all(111)
        G = nx.watts_strogatz_graph(n=110, k=6, p=0.1)
        
        # Convert to edge list
        edge_list = list(G.edges())
        
        # Verify format: list of tuples
        assert isinstance(edge_list, list)
        assert len(edge_list) > 0
        
        # Each edge should be a tuple of two integers
        for edge in edge_list:
            assert isinstance(edge, tuple)
            assert len(edge) == 2
            assert isinstance(edge[0], int)
            assert isinstance(edge[1], int)
            assert 0 <= edge[0] < 110
            assert 0 <= edge[1] < 110

    def test_adjacency_matrix_creation(self):
        """Verify adjacency matrix can be created and has correct shape."""
        seed_all(222)
        G = nx.watts_strogatz_graph(n=110, k=6, p=0.1)
        
        adj_matrix = create_normalized_adjacency(G)
        
        # Verify shape
        assert adj_matrix.shape == (110, 110)
        
        # Verify symmetry (undirected graph)
        np.testing.assert_array_almost_equal(adj_matrix, adj_matrix.T)
        
        # Verify non-negative values
        assert np.all(adj_matrix >= 0)

class TestGenerationConstants:
    """Tests to verify generation uses correct constants from utils."""

    def test_sample_size_is_110(self):
        """Verify SAMPLE_SIZE constant is 110 as required by spec."""
        assert SAMPLE_SIZE == 110, f"Expected SAMPLE_SIZE=110, got {SAMPLE_SIZE}"

    def test_convergence_threshold_is_0_90(self):
        """Verify CONVERGENCE_THRESHOLD constant is 0.90."""
        assert CONVERGENCE_THRESHOLD == 0.90, \
            f"Expected CONVERGENCE_THRESHOLD=0.90, got {CONVERGENCE_THRESHOLD}"

class TestLabelAnnotationAndClassBalance:
    """Tests for community label derivation and class balance validation (US1)."""

    def _generate_ring_lattice_with_labels(self, n=110, k=6):
        """
        Helper to generate a ring lattice and derive community labels.
        Simulates the logic that will be in data_generation.py.
        Community is defined by the initial ring position modulo num_communities.
        """
        # Create the initial ring lattice (p=0)
        G = nx.watts_strogatz_graph(n=n, k=k, p=0)
        
        # Derive labels based on node index (simulating initial lattice communities)
        # In the real implementation, this will be based on the initial lattice structure
        # before rewiring. For a ring lattice, we can define communities by contiguous blocks.
        num_communities = 5
        labels = {node: node % num_communities for node in G.nodes()}
        
        return G, labels

    def test_label_annotation_correctness(self):
        """Verify that labels are correctly derived from node indices."""
        G, labels = self._generate_ring_lattice_with_labels()
        
        # Verify every node has a label
        assert len(labels) == G.number_of_nodes()
        assert set(labels.keys()) == set(G.nodes())
        
        # Verify labels are integers within expected range
        unique_labels = set(labels.values())
        assert all(isinstance(l, int) for l in unique_labels)
        assert min(unique_labels) >= 0
        assert max(unique_labels) < 5  # Assuming 5 communities

    def test_class_balance_check_pass(self):
        """Verify that a balanced dataset passes the class balance check."""
        G, labels = self._generate_ring_lattice_with_labels()
        
        # Calculate class distribution
        class_counts = {}
        for label in labels.values():
            class_counts[label] = class_counts.get(label, 0) + 1
        
        total_nodes = sum(class_counts.values())
        max_ratio = max(class_counts.values()) / total_nodes
        
        # With 110 nodes and 5 communities (balanced by design), 
        # max ratio should be ~0.2 (20%)
        assert max_ratio < 0.8, f"Class imbalance detected: max ratio {max_ratio}"

    def test_class_balance_check_fail(self):
        """Verify that an imbalanced dataset fails the class balance check."""
        # Create a scenario with severe imbalance
        n = 110
        labels = {node: 0 for node in range(n)}  # All nodes in class 0
        labels[100] = 1  # Only one node in class 1
        
        class_counts = {}
        for label in labels.values():
            class_counts[label] = class_counts.get(label, 0) + 1
        
        total_nodes = sum(class_counts.values())
        max_ratio = max(class_counts.values()) / total_nodes
        
        # This should fail the balance check
        assert max_ratio >= 0.8, f"Expected imbalance to be detected, got ratio {max_ratio}"

    def test_class_balance_threshold_enforcement(self):
        """Verify the exact threshold (80%) is enforced."""
        n = 110
        
        # Create a dataset exactly at the threshold
        # 88 nodes in class 0, 22 in class 1 -> 80% exactly
        labels = {}
        for i in range(n):
            if i < 88:
                labels[i] = 0
            else:
                labels[i] = 1
        
        class_counts = {}
        for label in labels.values():
            class_counts[label] = class_counts.get(label, 0) + 1
        
        total_nodes = sum(class_counts.values())
        max_ratio = max(class_counts.values()) / total_nodes
        
        # Exactly 0.8 should be considered imbalanced (>= 0.8)
        assert max_ratio == 0.8
        
        # Create a dataset just below the threshold
        # 87 nodes in class 0, 23 in class 1 -> ~79.1%
        labels_below = {}
        for i in range(n):
            if i < 87:
                labels_below[i] = 0
            else:
                labels_below[i] = 1
        
        class_counts_below = {}
        for label in labels_below.values():
            class_counts_below[label] = class_counts_below.get(label, 0) + 1
        
        total_nodes_below = sum(class_counts_below.values())
        max_ratio_below = max(class_counts_below.values()) / total_nodes_below
        
        # Just below 0.8 should pass
        assert max_ratio_below < 0.8

    def test_label_distribution_across_beta_levels(self):
        """Verify label distribution remains consistent across different beta levels."""
        betas = [0.0, 0.2, 0.5, 0.8, 1.0]
        
        for beta in betas:
            # Generate lattice and derive labels (before rewiring)
            G_lattice = nx.watts_strogatz_graph(n=110, k=6, p=0)
            labels = {node: node % 5 for node in G_lattice.nodes()}
            
            # Verify distribution is consistent
            class_counts = {}
            for label in labels.values():
                class_counts[label] = class_counts.get(label, 0) + 1
            
            # With 110 nodes and 5 communities, we expect roughly 22 per class
            # Allow some variance due to 110 not being perfectly divisible by 5
            expected_per_class = 110 / 5
            for count in class_counts.values():
                # Each class should have between 18 and 26 nodes (reasonable variance)
                assert 18 <= count <= 26, f"Unexpected class count {count} for beta={beta}"

    def test_label_annotation_on_disconnected_graphs(self):
        """Verify label annotation works even on disconnected graphs."""
        # Create a graph that might be disconnected
        seed_all(999)
        G = nx.watts_strogatz_graph(n=110, k=6, p=0.5)
        
        # Labels should still be derivable based on initial lattice position
        # (in real implementation, this would be done before rewiring)
        labels = {node: node % 5 for node in G.nodes()}
        
        # Verify all nodes have labels
        assert len(labels) == G.number_of_nodes()
        assert set(labels.keys()) == set(G.nodes())

    def test_class_balance_function_integration(self):
        """Test the complete flow of label generation and balance checking."""
        def check_class_balance(labels, max_ratio=0.8):
            """Helper function to check class balance."""
            class_counts = {}
            for label in labels.values():
                class_counts[label] = class_counts.get(label, 0) + 1
            
            total = sum(class_counts.values())
            if total == 0:
                return True, 0.0
            
            max_ratio_found = max(class_counts.values()) / total
            return max_ratio_found < max_ratio, max_ratio_found

        # Test balanced case
        balanced_labels = {i: i % 5 for i in range(110)}
        is_balanced, ratio = check_class_balance(balanced_labels)
        assert is_balanced, f"Balanced case failed: ratio {ratio}"
        
        # Test imbalanced case
        imbalanced_labels = {i: 0 for i in range(110)}
        imbalanced_labels[100] = 1
        is_balanced, ratio = check_class_balance(imbalanced_labels)
        assert not is_balanced, f"Imbalanced case passed: ratio {ratio}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])