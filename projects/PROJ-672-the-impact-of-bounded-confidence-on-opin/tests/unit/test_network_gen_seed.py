"""
Unit tests for T012: Network Generation with Fixed Seeds.

This test verifies that the generate_networks module correctly uses the
global seed fixture defined in tests/conftest.py to produce reproducible results.
"""
import os
import sys
from pathlib import Path
import tempfile
import shutil

import pytest
import networkx as nx
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.generate_networks import (
    generate_erdos_renyi,
    generate_barabasi_albert,
    generate_watts_strogatz,
    ensure_connected,
    BASE_SEED
)

class TestSeedReproducibility:
    """Tests to ensure deterministic output given fixed seeds."""

    def test_erdos_renyi_deterministic(self):
        """Verify ER graph generation is deterministic with same seed."""
        seed = 12345
        G1 = generate_erdos_renyi(n=50, p=0.1, seed=seed)
        G2 = generate_erdos_renyi(n=50, p=0.1, seed=seed)
        
        # Compare edge sets
        assert set(G1.edges()) == set(G2.edges()), "ER graphs with same seed should be identical"
        assert G1.number_of_nodes() == G2.number_of_nodes()

    def test_barabasi_albert_deterministic(self):
        """Verify BA graph generation is deterministic with same seed."""
        seed = 54321
        G1 = generate_barabasi_albert(n=50, m=2, seed=seed)
        G2 = generate_barabasi_albert(n=50, m=2, seed=seed)
        
        assert set(G1.edges()) == set(G2.edges()), "BA graphs with same seed should be identical"

    def test_watts_strogatz_deterministic(self):
        """Verify WS graph generation is deterministic with same seed."""
        seed = 99999
        G1 = generate_watts_strogatz(n=50, k=4, p=0.1, seed=seed)
        G2 = generate_watts_strogatz(n=50, k=4, p=0.1, seed=seed)
        
        assert set(G1.edges()) == set(G2.edges()), "WS graphs with same seed should be identical"

    def test_base_seed_fixture_consistency(self):
        """Verify the imported BASE_SEED matches the environment or default."""
        expected = int(os.getenv("PROJECT_BASE_SEED", "42"))
        assert BASE_SEED == expected, f"BASE_SEED {BASE_SEED} does not match env {expected}"

class TestConnectivity:
    """Tests for the ensure_connected function."""

    def test_already_connected_unchanged(self):
        """Ensure a connected graph is returned unchanged."""
        G = nx.erdos_renyi_graph(50, 0.2, seed=42)
        # Force it to be connected by adding edges if necessary (simple way for test)
        while not nx.is_connected(G):
            G = nx.erdos_renyi_graph(50, 0.2, seed=42) # Retry until connected for test setup
        
        G_copy = G.copy()
        G_result = ensure_connected(G, "er")
        
        # Check identity of edges (should be same object if we didn't copy, but logic copies)
        # We check structural equality
        assert set(G_result.edges()) == set(G_copy.edges())
        assert nx.is_connected(G_result)

    def test_disconnected_graph_reconnected(self):
        """Ensure a disconnected graph is reconnected."""
        # Create a graph with two clear components
        G = nx.Graph()
        G.add_nodes_from(range(10))
        G.add_edges_from([(i, i+1) for i in range(0, 4)]) # Component 1: 0-1-2-3-4
        G.add_edges_from([(i, i+1) for i in range(5, 9)]) # Component 2: 5-6-7-8-9
        
        assert not nx.is_connected(G)
        
        G_fixed = ensure_connected(G, "er")
        
        assert nx.is_connected(G_fixed), "ensure_connected should make the graph connected"
        assert G_fixed.number_of_nodes() == G.number_of_nodes()