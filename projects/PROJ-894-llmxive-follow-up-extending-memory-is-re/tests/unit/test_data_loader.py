import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datasets import DatasetNotFoundError

# Import the module under test
# We assume the code is in the 'code' directory and we are running from the project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_loader import fetch_locomo_dataset, inject_noise, generate_noisy_graphs, save_noisy_graphs, load_noisy_graphs
import networkx as nx

class TestFetchLoCoMoDataset:
    def test_fetch_success(self):
        """Test that fetch_locomo_dataset succeeds when the dataset is available."""
        mock_data = [
            {"id": "1", "question": "Q1", "context": "C1", "answer": "A1"},
            {"id": "2", "question": "Q2", "context": "C2", "answer": "A2"}
        ]
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = lambda self: iter(mock_data)
        
        with patch('code.data_loader.load_dataset', return_value=mock_dataset):
            tasks = fetch_locomo_dataset(subset="test")
            
        assert len(tasks) == 2
        assert tasks[0]["task_id"] == "1"
        assert tasks[1]["question"] == "Q2"

    def test_fetch_failure_raises_value_error(self):
        """
        Test that fetch_locomo_dataset raises ValueError when the dataset fetch fails.
        This enforces T035: No silent fallback to synthetic data.
        """
        with patch('code.data_loader.load_dataset', side_effect=DatasetNotFoundError("Dataset not found")):
            with pytest.raises(ValueError) as excinfo:
                fetch_locomo_dataset(subset="test")
            
            assert "Dataset fetch failed" in str(excinfo.value)

class TestInjectNoise:
    def test_inject_noise_replaces_edges(self):
        """
        Test that inject_noise correctly replaces a proportion of edges.
        This is the primary test for T011b and T011c verification.
        """
        # Create a deterministic graph
        G = nx.DiGraph()
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
            (1, 3), (2, 4), (3, 5), (1, 5)
        ])
        
        original_edges = set(G.edges())
        original_count = len(original_edges)
        
        # Inject 50% noise with a fixed seed
        ratio = 0.5
        seed = 42
        noisy_G = inject_noise(G, ratio, seed)
        
        noisy_edges = set(noisy_G.edges())
        
        # Verify total edge count remains roughly the same
        assert noisy_G.number_of_edges() <= original_count + 1
        
        # Verify that not all original edges are preserved
        removed_count = original_count - len(original_edges & noisy_edges)
        assert removed_count > 0, "Expected some edges to be removed."
        
        # Verify that some new edges were added that were not in the original
        added_count = len(noisy_edges - original_edges)
        assert added_count > 0, "Expected some new edges to be added."
        
        # Verify reproducibility: running with same seed should produce same result
        noisy_G_2 = inject_noise(G, ratio, seed)
        assert set(noisy_G.edges()) == set(noisy_G_2.edges()), "Noise injection is not reproducible with same seed."

    def test_inject_noise_zero_ratio(self):
        """Test that 0 ratio results in identical graph."""
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3)])
        
        noisy_G = inject_noise(G, 0.0, 42)
        
        assert set(G.edges()) == set(noisy_G.edges())
        assert G.number_of_edges() == noisy_G.number_of_edges()

    def test_inject_noise_invalid_ratio(self):
        """Test that invalid ratio raises ValueError."""
        G = nx.DiGraph()
        G.add_edge(1, 2)
        
        with pytest.raises(ValueError):
            inject_noise(G, 1.5, 42)
        
        with pytest.raises(ValueError):
            inject_noise(G, -0.1, 42)

class TestGenerateNoisyGraphs:
    def test_generate_noisy_graphs_creates_output(self, tmp_path):
        """Test that generate_noisy_graphs creates a valid noisy graph set."""
        # Create a simple graph
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])
        graphs = {"task_1": G}
        
        noisy_graphs = generate_noisy_graphs(graphs, ratio=0.5, seed=42)
        
        assert len(noisy_graphs) == 1
        assert "task_1" in noisy_graphs
        assert isinstance(noisy_graphs["task_1"], nx.DiGraph)
        
        # Check that edges were modified (statistically likely with 50% noise)
        original_edges = set(G.edges())
        noisy_edges = set(noisy_graphs["task_1"].edges())
        # We don't assert they are different because it's probabilistic, but we can check structure
        assert noisy_graphs["task_1"].number_of_nodes() == G.number_of_nodes()

class TestSaveLoadNoisyGraphs:
    def test_save_and_load_noisy_graphs(self, tmp_path):
        """Test that noisy graphs can be saved and loaded correctly."""
        # Create a simple graph
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])
        graphs = {"task_1": G}
        
        noisy_graphs = generate_noisy_graphs(graphs, ratio=0.5, seed=42)
        
        output_path = tmp_path / "test_graph_noise.json"
        save_noisy_graphs(noisy_graphs, output_path=output_path)
        
        assert output_path.exists()
        
        loaded_graphs = load_noisy_graphs(input_path=output_path)
        
        assert len(loaded_graphs) == 1
        assert "task_1" in loaded_graphs
        assert set(loaded_graphs["task_1"].edges()) == set(noisy_graphs["task_1"].edges())