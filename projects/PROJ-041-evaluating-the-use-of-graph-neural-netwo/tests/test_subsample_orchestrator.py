import os
import tempfile
import pytest
import networkx as nx
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.subsample_orchestrator import (
    run_subsampling_orchestration,
    load_graph_safe,
    NODE_LIMIT
)
from utils.memory_monitor import MemoryLimitExceededError

class TestSubsampleOrchestrator:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_no_subsample_needed(self, temp_dir):
        """Test that a small graph passes through unchanged."""
        # Create a small graph
        G = nx.erdos_renyi_graph(100, 0.1, seed=42)
        input_path = os.path.join(temp_dir, "graph_small_raw.graphml")
        nx.write_graphml(G, input_path)

        output_path, hash_path = run_subsampling_orchestration(
            raw_graph_path=input_path,
            seed=42,
            output_dir=temp_dir,
            node_limit=5000
        )

        assert os.path.exists(output_path)
        assert os.path.exists(hash_path)
        
        # Verify content
        G_out = nx.read_graphml(output_path)
        assert G_out.number_of_nodes() == 100

    def test_lcc_subsample_only(self, temp_dir):
        """Test graph that needs LCC but LCC is within limits."""
        # Create a graph with a large component and some isolated nodes
        G_full = nx.Graph()
        # Large component
        large_comp = nx.erdos_renyi_graph(3000, 0.1, seed=42)
        # Add some isolated nodes
        for i in range(1000):
            G_full.add_node(f"isolated_{i}")
        
        # Map nodes of large_comp to G_full
        mapping = {n: f"comp_{n}" for n in large_comp.nodes()}
        G_full.add_nodes_from(mapping.values())
        G_full.add_edges_from([(mapping[u], mapping[v]) for u, v in large_comp.edges()])
        
        input_path = os.path.join(temp_dir, "graph_lcc_test_raw.graphml")
        nx.write_graphml(G_full, input_path)

        output_path, hash_path = run_subsampling_orchestration(
            raw_graph_path=input_path,
            seed=42,
            output_dir=temp_dir,
            node_limit=5000
        )

        assert os.path.exists(output_path)
        G_out = nx.read_graphml(output_path)
        # Should be the LCC (approx 3000 nodes)
        assert G_out.number_of_nodes() <= 5000
        assert G_out.number_of_nodes() < G_full.number_of_nodes()

    def test_degree_subsample_fallback(self, temp_dir):
        """Test graph where LCC is still too big, requiring degree subsampling."""
        # Create a graph with > 5000 nodes in LCC
        # Use a scale-free graph to ensure high degree nodes exist
        G = nx.barabasi_albert_graph(6000, 5, seed=42)
        
        input_path = os.path.join(temp_dir, "graph_degree_test_raw.graphml")
        nx.write_graphml(G, input_path)

        output_path, hash_path = run_subsampling_orchestration(
            raw_graph_path=input_path,
            seed=42,
            output_dir=temp_dir,
            node_limit=5000
        )

        assert os.path.exists(output_path)
        G_out = nx.read_graphml(output_path)
        # Should be exactly or close to the limit
        assert G_out.number_of_nodes() <= 5000
        assert G_out.number_of_nodes() < 6000

    def test_missing_input_file(self, temp_dir):
        """Test that FileNotFoundError is raised for missing input."""
        with pytest.raises(FileNotFoundError):
            run_subsampling_orchestration(
                raw_graph_path=os.path.join(temp_dir, "nonexistent.graphml"),
                seed=42,
                output_dir=temp_dir
            )

    def test_memory_limit_exceeded(self, temp_dir, monkeypatch):
        """Test that MemoryLimitExceededError is raised if memory is too high."""
        # Create a dummy graph
        G = nx.erdos_renyi_graph(100, 0.1, seed=42)
        input_path = os.path.join(temp_dir, "graph_mem_test_raw.graphml")
        nx.write_graphml(G, input_path)

        # Mock the memory monitor to return a high value
        with patch('data.subsample_orchestrator.stop_monitoring', return_value=10000.0): # 10GB
            with pytest.raises(MemoryLimitExceededError):
                run_subsampling_orchestration(
                    raw_graph_path=input_path,
                    seed=42,
                    output_dir=temp_dir,
                    memory_limit_gb=7.0
                )
