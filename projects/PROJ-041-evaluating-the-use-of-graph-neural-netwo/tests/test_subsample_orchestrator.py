"""
Tests for the Subsampling Orchestrator (T008d).

Validates the decision tree logic:
1. Graphs under limit are passed through.
2. Graphs over limit trigger LCC extraction.
3. LCCs over limit trigger degree-based subsampling.
"""

import os
import sys
import tempfile
import shutil
import networkx as nx
import pytest

# Add project root to path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from data.subsample_orchestrator import (
    run_subsampling_orchestration,
    extract_lcc,
    degree_based_subsample,
    NODE_LIMIT,
    MEMORY_LIMIT_MB
)
from utils.seed import set_seed

@pytest.fixture
def temp_graph_dir():
    """Create a temporary directory for test graphs."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

def create_test_graph(num_nodes, num_edges, connected=True):
    """Helper to create a test graph."""
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    if connected and num_nodes > 1:
        # Create a path to ensure connectivity
        G.add_edges_from([(i, i+1) for i in range(num_nodes-1)])
        # Add random edges
        for _ in range(max(0, num_edges - (num_nodes - 1))):
            u = np.random.randint(0, num_nodes)
            v = np.random.randint(0, num_nodes)
            if u != v and not G.has_edge(u, v):
                G.add_edge(u, v)
    else:
        # Disconnected graph
        for _ in range(num_edges):
            u = np.random.randint(0, num_nodes)
            v = np.random.randint(0, num_nodes)
            if u != v and not G.has_edge(u, v):
                G.add_edge(u, v)
    return G

import numpy as np

class TestSubsamplingOrchestrator:
    def test_graph_under_limit_passes_through(self, temp_graph_dir):
        """Test that a graph under 5000 nodes is copied directly."""
        input_path = os.path.join(temp_graph_dir, "input.graphml")
        output_path = os.path.join(temp_graph_dir, "output.graphml")

        G = create_test_graph(1000, 2000)
        nx.write_graphml(G, input_path)

        result_path = run_subsampling_orchestration(input_path, output_path, seed=42)

        assert os.path.exists(result_path)
        assert os.path.exists(result_path + ".hash")
        
        # Verify node count is preserved
        G_out = nx.read_graphml(result_path)
        assert G_out.number_of_nodes() == 1000

    def test_large_graph_triggers_lcc(self, temp_graph_dir):
        """Test that a large graph triggers LCC extraction."""
        input_path = os.path.join(temp_graph_dir, "input.graphml")
        output_path = os.path.join(temp_graph_dir, "output.graphml")

        # Create a graph with > 5000 nodes
        G = create_test_graph(6000, 12000)
        nx.write_graphml(G, input_path)

        result_path = run_subsampling_orchestration(input_path, output_path, seed=42)

        assert os.path.exists(result_path)
        G_out = nx.read_graphml(result_path)
        
        # Should be <= 5000
        assert G_out.number_of_nodes() <= NODE_LIMIT

    def test_disconnected_graph_lcc_extraction(self, temp_graph_dir):
        """Test LCC extraction on a disconnected graph."""
        input_path = os.path.join(temp_graph_dir, "input.graphml")
        output_path = os.path.join(temp_graph_dir, "output.graphml")

        # Create a graph with two large components
        G = nx.Graph()
        # Component 1: 6000 nodes
        comp1 = list(range(6000))
        G.add_nodes_from(comp1)
        G.add_edges_from([(i, i+1) for i in range(5999)])
        
        # Component 2: 1000 nodes
        comp2 = list(range(6000, 7000))
        G.add_nodes_from(comp2)
        G.add_edges_from([(i, i+1) for i in range(6000, 6999)])

        nx.write_graphml(G, input_path)

        result_path = run_subsampling_orchestration(input_path, output_path, seed=42)

        G_out = nx.read_graphml(result_path)
        
        # Should contain the LCC (6000 nodes) but wait, 6000 > 5000
        # So it should trigger degree subsampling on the LCC
        assert G_out.number_of_nodes() <= NODE_LIMIT

    def test_degree_subsample_tie_breaking(self, temp_graph_dir):
        """Test that degree subsampling uses IP string for tie-breaking."""
        # This is a unit test for the helper function logic
        # Create a graph where many nodes have the same degree
        G = nx.Graph()
        nodes = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4"]
        G.add_nodes_from(nodes)
        # Make them all have degree 1 (connected to a central hub not in list? No, simple ring)
        G.add_edges_from([("10.0.0.1", "10.0.0.2"), ("10.0.0.3", "10.0.0.4")])
        
        # All have degree 1.
        # We want to select 2.
        # Tie-breaking: sort by degree (desc), then by IP (asc).
        # Sorted: 10.0.0.1, 10.0.0.2, 10.0.0.3, 10.0.0.4
        # Select top 2: 10.0.0.1, 10.0.0.2
        
        subsampled = degree_based_subsample(G, 2, seed=42)
        assert subsampled.number_of_nodes() == 2
        assert "10.0.0.1" in subsampled.nodes()
        assert "10.0.0.2" in subsampled.nodes()
        assert "10.0.0.3" not in subsampled.nodes()

    def test_lcc_extraction_on_empty_graph(self, temp_graph_dir):
        """Test LCC extraction on an empty graph."""
        input_path = os.path.join(temp_graph_dir, "input.graphml")
        output_path = os.path.join(temp_graph_dir, "output.graphml")

        G = nx.Graph()
        nx.write_graphml(G, input_path)

        result_path = run_subsampling_orchestration(input_path, output_path, seed=42)
        
        # Should handle gracefully
        assert os.path.exists(result_path)
        G_out = nx.read_graphml(result_path)
        assert G_out.number_of_nodes() == 0