"""
Unit tests for data_loader module.
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil

# Import the module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import (
    ensure_output_dirs,
    generate_noisy_graphs,
    save_noisy_graphs,
    NOISE_PROPORTION,
    RANDOM_SEED
)
from graph_utils import build_memory_graph

def test_generate_noisy_graphs_basic():
    """Test basic noisy graph generation."""
    # Create sample tasks
    tasks = [
        {
            "task_id": "test_1",
            "question": "What is the capital?",
            "context": "The capital of France is Paris. Paris is a beautiful city.",
            "answer": "Paris"
        },
        {
            "task_id": "test_2", 
            "question": "Who wrote the book?",
            "context": "John wrote a book about history. The book was published in 2020.",
            "answer": "John"
        }
    ]
    
    # Generate noisy graphs
    noisy_tasks = generate_noisy_graphs(
        tasks,
        noise_proportion=0.1,
        seed=42
    )
    
    # Verify results
    assert len(noisy_tasks) == len(tasks)
    
    for task in noisy_tasks:
        assert "noisy_graph" in task
        assert "original_graph" in task
        assert task["noise_proportion"] == 0.1
        
        # Check that graphs are not None
        assert task["noisy_graph"] is not None
        assert task["original_graph"] is not None
        
        # Check graph structure
        assert "nodes" in task["noisy_graph"]
        assert "edges" in task["noisy_graph"]
        assert "nodes" in task["original_graph"]
        assert "edges" in task["original_graph"]

def test_generate_noisy_graphs_zero_noise():
    """Test that zero noise returns original graphs."""
    tasks = [
        {
            "task_id": "test_1",
            "question": "Test question",
            "context": "Test context with some words.",
            "answer": "Test answer"
        }
    ]
    
    noisy_tasks = generate_noisy_graphs(
        tasks,
        noise_proportion=0.0,
        seed=42
    )
    
    # With zero noise, graphs should be identical
    original_graph = tasks[0]["context"]  # Just use context as reference
    noisy_graph = noisy_tasks[0]["noisy_graph"]
    original_graph_data = noisy_tasks[0]["original_graph"]
    
    # Both should have same number of nodes and edges
    assert len(noisy_graph["nodes"]) == len(original_graph_data["nodes"])
    assert len(noisy_graph["edges"]) == len(original_graph_data["edges"])

def test_generate_noisy_graphs_invalid_proportion():
    """Test that invalid noise proportion raises error."""
    tasks = [
        {
            "task_id": "test_1",
            "question": "Test",
            "context": "Test context.",
            "answer": "Test"
        }
    ]
    
    with pytest.raises(ValueError):
        generate_noisy_graphs(
            tasks,
            noise_proportion=1.5,  # Invalid: > 1.0
            seed=42
        )
    
    with pytest.raises(ValueError):
        generate_noisy_graphs(
            tasks,
            noise_proportion=-0.1,  # Invalid: < 0.0
            seed=42
        )

def test_reproducibility():
    """Test that same seed produces same results."""
    tasks = [
        {
            "task_id": "test_1",
            "question": "Test question",
            "context": "This is a test context with multiple words for graph building.",
            "answer": "Test"
        }
    ]
    
    # Generate twice with same seed
    noisy_tasks_1 = generate_noisy_graphs(tasks, noise_proportion=0.1, seed=123)
    noisy_tasks_2 = generate_noisy_graphs(tasks, noise_proportion=0.1, seed=123)
    
    # Results should be identical
    assert noisy_tasks_1[0]["noisy_graph"] == noisy_tasks_2[0]["noisy_graph"]

def test_save_and_load_noisy_graphs():
    """Test saving and loading noisy graphs."""
    tasks = [
        {
            "task_id": "test_1",
            "question": "Test",
            "context": "Test context with words.",
            "answer": "Test"
        }
    ]
    
    noisy_tasks = generate_noisy_graphs(tasks, noise_proportion=0.1, seed=42)
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Temporarily override the GRAPHS_DIR
        import data_loader
        original_graphs_dir = data_loader.GRAPHS_DIR
        data_loader.GRAPHS_DIR = tmp_path / "graphs"
        data_loader.GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save noisy graphs
            data_loader.save_noisy_graphs(noisy_tasks, "test_noisy.json")
            
            # Verify file exists
            output_file = tmp_path / "graphs" / "test_noisy.json"
            assert output_file.exists()
            
            # Load and verify content
            with open(output_file, 'r') as f:
                loaded_data = json.load(f)
            
            assert len(loaded_data) == len(noisy_tasks)
            assert loaded_data[0]["task_id"] == "test_1"
            
        finally:
            # Restore original directory
            data_loader.GRAPHS_DIR = original_graphs_dir
