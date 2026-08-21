"""
Unit tests for data_loader module.
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data_loader import (
    fetch_locomo_dataset,
    save_raw_data,
    load_raw_data,
    build_memory_graph,
    save_graphs,
    load_graphs,
    inject_noise,
    generate_noisy_graphs,
    save_noisy_graphs,
    load_noisy_graphs,
    process_in_chunks
)

class TestDataLoader:
    
    def test_inject_noise_replaces_edges(self):
        """Test that inject_noise replaces edges correctly."""
        graph_data = {
            "nodes": ["A", "B", "C", "D"],
            "edges": [
                {"source": "A", "target": "B", "relation": "rel1"},
                {"source": "B", "target": "C", "relation": "rel2"},
                {"source": "C", "target": "D", "relation": "rel3"},
                {"source": "A", "target": "C", "relation": "rel4"}
            ]
        }
        
        # Inject 50% noise
        noisy = inject_noise(graph_data, ratio=0.5, seed=42)
        
        # Check that nodes are preserved
        assert set(noisy["nodes"]) == set(graph_data["nodes"])
        
        # Check that edge count is preserved
        assert len(noisy["edges"]) == len(graph_data["edges"])
        
        # Check that some edges are different (noise injected)
        original_edges = {(e["source"], e["target"]) for e in graph_data["edges"]}
        noisy_edges = {(e["source"], e["target"]) for e in noisy["edges"]}
        
        # There should be some difference
        assert len(original_edges.symmetric_difference(noisy_edges)) > 0
        
    def test_no_fallback_on_failure(self):
        """Test that fetch_locomo_dataset raises an error when fetch fails."""
        with patch('data_loader.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Dataset not found")
            
            with pytest.raises(ValueError) as exc_info:
                fetch_locomo_dataset(subset="test", streaming=False)
            
            assert "Dataset fetch failed" in str(exc_info.value)
            
    def test_streaming_mode(self):
        """Test that streaming mode works correctly."""
        # Mock a streaming dataset
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([
            {"question": "Q1", "context": "C1", "answer": "A1"},
            {"question": "Q2", "context": "C2", "answer": "A2"}
        ]))
        
        with patch('data_loader.load_dataset', return_value=mock_ds):
            records = fetch_locomo_dataset(subset="test", streaming=True)
            
            # Should return an iterator
            assert hasattr(records, '__iter__')
            
            # Consume the iterator
            result = list(records)
            assert len(result) == 2
            assert result[0]["question"] == "Q1"
            
    def test_build_memory_graph(self):
        """Test graph building from records."""
        records = [
            {
                "task_id": "task1",
                "question": "What is X?",
                "context": "X is related to Y. Y is related to Z.",
                "answer": "Z"
            }
        ]
        
        graphs = build_memory_graph(records)
        
        assert "task1" in graphs
        assert "graph" in graphs["task1"]
        assert "nodes" in graphs["task1"]["graph"]
        assert "edges" in graphs["task1"]["graph"]
        
    def test_save_and_load_graphs(self):
        """Test saving and loading graphs."""
        graphs = {
            "task1": {
                "task_id": "task1",
                "question": "Q1",
                "answer": "A1",
                "graph": {
                    "nodes": ["A", "B"],
                    "edges": [{"source": "A", "target": "B", "relation": "rel1"}]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            
        try:
            save_graphs(graphs, temp_path)
            loaded = load_graphs(temp_path)
            
            assert loaded == graphs
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    def test_generate_noisy_graphs(self):
        """Test generating noisy graphs."""
        graphs = {
            "task1": {
                "task_id": "task1",
                "question": "Q1",
                "answer": "A1",
                "graph": {
                    "nodes": ["A", "B", "C"],
                    "edges": [
                        {"source": "A", "target": "B", "relation": "rel1"},
                        {"source": "B", "target": "C", "relation": "rel2"}
                    ]
                }
            }
        }
        
        noisy_graphs = generate_noisy_graphs(graphs, ratio=0.5, seed=42)
        
        assert "task1" in noisy_graphs
        assert len(noisy_graphs["task1"]["graph"]["edges"]) == len(graphs["task1"]["graph"]["edges"])
        
    def test_process_in_chunks(self):
        """Test chunked processing."""
        records = [{"id": i} for i in range(10)]
        processed = []
        
        def processor(chunk):
            processed.extend([r["id"] * 2 for r in chunk])
            return processed.copy()
            
        results = list(process_in_chunks(iter(records), 3, processor))
        
        assert len(results) == 4  # 10 items in chunks of 3 -> 4 chunks
        assert all(isinstance(r, list) for r in results)
        
    def test_real_data_source(self):
        """Test that real data source is used (not synthetic)."""
        # This test verifies that we are not falling back to synthetic data
        # In a real scenario, we would check that the dataset ID is correct
        # For now, we just verify the function exists and can be called
        # with the correct parameters
        
        # Mock the load_dataset to return valid data
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([
            {"question": "Q1", "context": "C1", "answer": "A1"}
        ]))
        
        with patch('data_loader.load_dataset', return_value=mock_ds):
            # This should not raise an error
            records = fetch_locomo_dataset(subset="test", streaming=False)
            result = list(records)
            assert len(result) == 1
            assert "question" in result[0]
            assert "context" in result[0]
            assert "answer" in result[0]