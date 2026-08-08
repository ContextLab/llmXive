"""
Unit tests for data_loader module.
Focuses on strict data fetching behavior and noise injection logic.
"""
import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_loader import (
    fetch_locomo_dataset,
    save_raw_data,
    build_memory_graph,
    inject_noise,
    generate_noisy_graphs,
    save_noisy_graphs,
    load_noisy_graphs,
    ensure_output_dirs
)
from datasets.exceptions import DatasetNotFoundError


class TestStrictDataFetching:
    """Tests to verify that data fetching fails loudly without synthetic fallback."""

    def test_fetch_locomo_dataset_raises_on_failure(self):
        """
        Verify that fetch_locomo_dataset raises an exception when the dataset
        is unavailable, rather than returning synthetic data.
        """
        # Mock load_dataset to raise a specific error
        with patch('data_loader.load_dataset') as mock_load:
            mock_load.side_effect = DatasetNotFoundError(
                "Dataset 'locomo/locomo-benchmark' doesn't exist."
            )
            
            # Should raise RuntimeError, not return synthetic data
            with pytest.raises(RuntimeError) as exc_info:
                fetch_locomo_dataset(subset="test")
            
            assert "CRITICAL" in str(exc_info.value)
            assert "Failed to fetch real data" in str(exc_info.value)
            assert "fabrication" in str(exc_info.value).lower()

    def test_fetch_locomo_dataset_raises_on_connection_error(self):
        """
        Verify that connection errors also cause a loud failure.
        """
        with patch('data_loader.load_dataset') as mock_load:
            mock_load.side_effect = ConnectionError("Network unreachable")
            
            with pytest.raises(RuntimeError) as exc_info:
                fetch_locomo_dataset(subset="test")
            
            assert "CRITICAL" in str(exc_info.value)

    def test_no_synthetic_fallback_in_fetch(self):
        """
        Ensure that the fetch function does NOT contain any try/except blocks
        that return synthetic data on failure.
        """
        import inspect
        source = inspect.getsource(fetch_locomo_dataset)
        
        # Check for common patterns of synthetic fallback
        forbidden_patterns = [
            "return generate_synthetic",
            "return mock_data",
            "return fake",
            "return [] # synthetic",
            "return [{}] # placeholder"
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in source, (
                f"Found forbidden pattern '{pattern}' in fetch_locomo_dataset. "
                "Strict data fetching requires NO synthetic fallbacks."
            )


class TestNoiseInjection:
    """Tests for noise injection logic."""

    def test_inject_noise_adds_edges(self):
        """
        Verify that inject_noise ADDS edges to the graph,
        rather than replacing existing ones.
        """
        import networkx as nx
        
        # Create a simple graph
        G = nx.DiGraph()
        G.add_edge("A", "B", relation_string="rel1")
        G.add_edge("B", "C", relation_string="rel2")
        
        original_edges = G.number_of_edges()
        
        # Inject noise with ratio 1.0 (should double edges roughly)
        noisy_G = inject_noise(G, ratio=1.0, seed=42)
        
        # Must have MORE edges
        assert noisy_G.number_of_edges() > original_edges
        
        # Original edges must still exist
        assert noisy_G.has_edge("A", "B")
        assert noisy_G.has_edge("B", "C")

    def test_inject_noise_reproducibility(self):
        """
        Verify that the same seed produces the same noise.
        """
        import networkx as nx
        
        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        G.add_edge("C", "D")
        
        # Generate twice with same seed
        noisy_1 = inject_noise(G, ratio=0.5, seed=123)
        noisy_2 = inject_noise(G, ratio=0.5, seed=123)
        
        # Compare edge sets
        edges_1 = set(noisy_1.edges())
        edges_2 = set(noisy_2.edges())
        
        assert edges_1 == edges_2, "Same seed must produce identical noise"

    def test_inject_noise_different_seeds(self):
        """
        Verify that different seeds produce different noise (with high probability).
        """
        import networkx as nx
        
        G = nx.DiGraph()
        # Create a larger graph to ensure randomness has effect
        for i in range(10):
            for j in range(i+1, 10):
                if i != j:
                    G.add_edge(f"n{i}", f"n{j}")
        
        noisy_1 = inject_noise(G, ratio=0.2, seed=42)
        noisy_2 = inject_noise(G, ratio=0.2, seed=999)
        
        edges_1 = set(noisy_1.edges())
        edges_2 = set(noisy_2.edges())
        
        # They should likely be different
        # Note: There is a tiny chance they could be the same, but with this graph size
        # and ratio, it's statistically improbable.
        assert edges_1 != edges_2, "Different seeds should produce different noise"

    def test_inject_noise_no_self_loops(self):
        """
        Verify that noise injection does not create self-loops.
        """
        import networkx as nx
        
        G = nx.DiGraph()
        G.add_edge("A", "B")
        
        noisy_G = inject_noise(G, ratio=10.0, seed=42)  # High ratio to force many attempts
        
        # Check for self-loops
        for node in noisy_G.nodes():
            assert not noisy_G.has_edge(node, node), "Self-loops must not be created"


class TestGraphConstruction:
    """Tests for graph construction from text."""

    def test_build_memory_graph_creates_nodes_and_edges(self):
        """
        Verify that build_memory_graph creates a valid graph with nodes and edges.
        """
        context = "The cat chased the mouse. The mouse ran away."
        
        G = build_memory_graph(context, task_id="test_001")
        
        assert G.number_of_nodes() > 0
        assert G.number_of_edges() > 0
        assert "test_001" in G.nodes()

    def test_build_memory_graph_handles_empty_context(self):
        """
        Verify behavior with empty context.
        """
        G = build_memory_graph("", task_id="empty_001")
        
        # Should at least have the task_id node
        assert "empty_001" in G.nodes()
        # Might have no other nodes/edges if parsing fails
        assert isinstance(G, type(nx.DiGraph()))


class TestIO:
    """Tests for save/load functionality."""

    def test_save_and_load_noisy_graphs(self):
        """
        Verify that graphs can be saved to JSON and loaded back correctly.
        """
        import networkx as nx
        
        # Create test graphs
        graphs = {}
        G1 = nx.DiGraph()
        G1.add_edge("A", "B", relation_string="rel1")
        G1.add_edge("B", "C", relation_string="rel2")
        
        G2 = nx.DiGraph()
        G2.add_edge("X", "Y", relation_string="rel3")
        
        graphs["task_1"] = G1
        graphs["task_2"] = G2
        
        # Save to temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_graphs.json"
            save_noisy_graphs(graphs, output_path)
            
            # Load back
            loaded_graphs = load_noisy_graphs(output_path)
            
            # Verify
            assert "task_1" in loaded_graphs
            assert "task_2" in loaded_graphs
            assert loaded_graphs["task_1"].number_of_edges() == 2
            assert loaded_graphs["task_2"].number_of_edges() == 1
            
            # Check edge attributes
            assert loaded_graphs["task_1"].edges[("A", "B")]["relation_string"] == "rel1"

    def test_load_nonexistent_file_raises(self):
        """
        Verify that loading from a nonexistent file raises FileNotFoundError.
        """
        with pytest.raises(FileNotFoundError):
            load_noisy_graphs(Path("/nonexistent/path/graphs.json"))


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_generate_noisy_graphs_end_to_end(self):
        """
        Test the full flow: tasks -> graphs -> noisy graphs -> save.
        """
        # Mock tasks
        tasks = [
            {"task_id": "t1", "question": "Q1", "context": "The dog barked at the mailman.", "answer": "A1"},
            {"task_id": "t2", "question": "Q2", "context": "The sun rose in the east.", "answer": "A2"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set output path to temp dir
            output_path = Path(tmpdir) / "integration_test.json"
            
            graphs = generate_noisy_graphs(tasks, ratio=0.1, seed=42)
            save_noisy_graphs(graphs, output_path)
            
            # Verify file exists
            assert output_path.exists()
            
            # Verify content
            loaded = load_noisy_graphs(output_path)
            assert "t1" in loaded
            assert "t2" in loaded
            assert loaded["t1"].number_of_nodes() > 0
            assert loaded["t2"].number_of_nodes() > 0