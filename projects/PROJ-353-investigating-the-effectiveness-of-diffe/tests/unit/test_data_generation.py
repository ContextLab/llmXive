import pytest
import networkx as nx
import numpy as np
import json
import os
from pathlib import Path

from code.data_generation import (
    generate_watts_strogatz_graph,
    derive_community_labels,
    compute_clustering_coefficient,
    validate_graph,
    BETA_LEVELS,
    GRAPHS_PER_BETA,
    NODE_COUNT
)
from code.utils import seed_all, SAMPLE_SIZE

class TestWattsStrogatzGeneration:
    """Unit tests for Watts-Strogatz generation logic (T017)."""

    def test_generate_connected_graph(self):
        """Test that generated graphs are connected for low beta."""
        seed_all(42)
        G = generate_watts_strogatz_graph(beta=0.0, seed=123)
        assert nx.is_connected(G), "Graph with beta=0.0 should be connected (ring lattice)"
        assert len(G.nodes()) == NODE_COUNT

    def test_generate_rewired_graph(self):
        """Test that generated graphs have correct node count with rewiring."""
        seed_all(42)
        G = generate_watts_strogatz_graph(beta=0.5, seed=456)
        assert len(G.nodes()) == NODE_COUNT
        # Graph might be disconnected for high beta, so we don't assert connectivity here

    def test_beta_levels_range(self):
        """Test that beta levels cover the full spectrum 0.0 to 1.0."""
        assert BETA_LEVELS == [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

class TestLabelAnnotation:
    """Unit tests for label annotation and class balance check (T018)."""

    def test_derive_labels_structure(self):
        """Test that labels are derived correctly from ring lattice."""
        seed_all(42)
        G = generate_watts_strogatz_graph(beta=0.0, seed=789)
        labels = derive_community_labels(G)
        
        assert len(labels) == NODE_COUNT
        assert all(0 <= l <= 3 for l in labels), "Labels should be in range [0, 3]"
        
        # Check that labels are assigned in blocks of 5 (20 nodes / 4 communities)
        expected_labels = [0]*5 + [1]*5 + [2]*5 + [3]*5
        assert list(labels) == expected_labels, "Labels should follow ring lattice structure"

    def test_class_balance_check(self):
        """Test that class balance is enforced (<80% max)."""
        # For 20 nodes and 4 communities, max class ratio is 5/20 = 0.25, which is < 0.8
        seed_all(42)
        G = generate_watts_strogatz_graph(beta=0.0, seed=999)
        labels = derive_community_labels(G)
        
        unique, counts = np.unique(labels, return_counts=True)
        max_ratio = max(counts) / len(labels)
        assert max_ratio < 0.8, f"Class balance check failed: max ratio {max_ratio} >= 0.8"

    def test_validate_graph_function(self):
        """Test the validate_graph function for connectivity and node count."""
        seed_all(42)
        G_connected = generate_watts_strogatz_graph(beta=0.0, seed=111)
        assert validate_graph(G_connected), "Connected graph should validate"

        # Create a disconnected graph manually to test failure
        G_disconnected = nx.Graph()
        G_disconnected.add_nodes_from(range(NODE_COUNT))
        G_disconnected.add_edges_from([(0, 1), (1, 2)])  # Only a small component
        assert not validate_graph(G_disconnected), "Disconnected graph should fail validation"

class TestIntegration:
    """Integration tests for the generation pipeline."""

    def test_sample_size_consistency(self):
        """Verify that SAMPLE_SIZE matches the expected total graphs."""
        # SAMPLE_SIZE is 110 (from utils.py)
        # Total graphs = 11 beta levels * 10 graphs/level = 110
        assert SAMPLE_SIZE == 110
        assert len(BETA_LEVELS) * GRAPHS_PER_BETA == 110

    def test_clustering_coefficient_positive(self):
        """Test that clustering coefficient is computed and positive for low beta."""
        seed_all(42)
        G = generate_watts_strogatz_graph(beta=0.0, seed=222)
        cc = compute_clustering_coefficient(G)
        assert cc > 0.0, "Clustering coefficient should be positive for ring lattice"
        # For k=2, n=20, beta=0, theoretical cc is approx 0.75
        assert cc <= 1.0, "Clustering coefficient should be <= 1.0"