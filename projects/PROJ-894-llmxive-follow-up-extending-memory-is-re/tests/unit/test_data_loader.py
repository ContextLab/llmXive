"""
Unit tests for data_loader module.

This test suite verifies that the data_loader module:
1. Correctly generates noisy graphs when given valid input.
2. Raises appropriate errors for invalid noise proportions.
3. Produces reproducible results with the same seed.
4. Correctly saves and loads noisy graphs.
5. FAILS LOUDLY when provided with an invalid dataset ID (T035 requirement).
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil
import sys

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import (
    ensure_output_dirs,
    generate_noisy_graphs,
    save_noisy_graphs,
    load_noisy_graphs,
    NOISE_PROPORTION,
    RANDOM_SEED
)
from graph_utils import build_memory_graph

# Mock the fetch_locomo_dataset to avoid network calls in unit tests
# We test the graph generation logic in isolation
def mock_fetch_locomo_dataset(subset=None):
    """Return a small set of mock tasks for testing graph generation."""
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
    if subset is not None:
        return tasks[:subset]
    return tasks

def test_generate_noisy_graphs_basic():
    """Test basic noisy graph generation."""
    tasks = mock_fetch_locomo_dataset()
    
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
    tasks = mock_fetch_locomo_dataset()
    
    noisy_tasks = generate_noisy_graphs(
        tasks,
        noise_proportion=0.0,
        seed=42
    )
    
    # With zero noise, graphs should be identical
    for i, task in enumerate(tasks):
        original_graph = noisy_tasks[i]["original_graph"]
        noisy_graph = noisy_tasks[i]["noisy_graph"]
        
        # Both should have same number of nodes and edges
        assert len(noisy_graph["nodes"]) == len(original_graph["nodes"])
        assert len(noisy_graph["edges"]) == len(original_graph["edges"])

def test_generate_noisy_graphs_invalid_proportion():
    """Test that invalid noise proportion raises error."""
    tasks = mock_fetch_locomo_dataset()
    
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
    tasks = mock_fetch_locomo_dataset()
    
    # Generate twice with same seed
    noisy_tasks_1 = generate_noisy_graphs(tasks, noise_proportion=0.1, seed=123)
    noisy_tasks_2 = generate_noisy_graphs(tasks, noise_proportion=0.1, seed=123)
    
    # Results should be identical
    assert noisy_tasks_1[0]["noisy_graph"] == noisy_tasks_2[0]["noisy_graph"]
    assert noisy_tasks_1[0]["original_graph"] == noisy_tasks_2[0]["original_graph"]

def test_save_and_load_noisy_graphs():
    """Test saving and loading noisy graphs."""
    tasks = mock_fetch_locomo_dataset()
    
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
            save_noisy_graphs(noisy_tasks, "test_noisy.json")
            
            # Verify file exists
            output_file = tmp_path / "graphs" / "test_noisy.json"
            assert output_file.exists()
            
            # Load and verify content
            loaded_data = load_noisy_graphs("test_noisy.json")
            
            assert len(loaded_data) == len(noisy_tasks)
            assert loaded_data[0]["task_id"] == "test_1"
            
        finally:
            # Restore original directory
            data_loader.GRAPHS_DIR = original_graphs_dir

def test_fetch_locomo_dataset_raises_on_invalid_id(monkeypatch):
    """
    T035: Test that fetch_locomo_dataset raises an exception when the 
    dataset ID is invalid, rather than falling back to synthetic data.
    
    This verifies the strict data fetching requirement.
    """
    import data_loader
    from datasets import DatasetNotFoundError
    
    # We can't easily mock the actual HuggingFace call in a unit test
    # without potentially hitting the network, so we test the error handling
    # by patching the load_dataset function to raise an error.
    
    original_load_dataset = data_loader.load_dataset
    
    def mock_load_dataset_fail(path, *args, **kwargs):
        raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist.")
    
    # Patch the function
    data_loader.load_dataset = mock_load_dataset_fail
    
    try:
        # This should raise a RuntimeError, not return synthetic data
        with pytest.raises(RuntimeError) as exc_info:
            data_loader.fetch_locomo_dataset(subset=1)
        
        # Verify the error message mentions the dataset ID and fabrication prevention
        error_msg = str(exc_info.value)
        assert "locomo/locomo-benchmark" in error_msg or "Dataset" in error_msg
        assert "fabrication" in error_msg.lower() or "halted" in error_msg.lower()
        
    finally:
        # Restore original function
        data_loader.load_dataset = original_load_dataset

def test_fetch_locomo_dataset_raises_on_network_error(monkeypatch):
    """
    T035: Test that fetch_locomo_dataset raises an exception on network errors,
    rather than falling back to synthetic data.
    """
    import data_loader
    
    original_load_dataset = data_loader.load_dataset
    
    def mock_load_dataset_network_error(path, *args, **kwargs):
        raise ConnectionError("Network is unreachable.")
    
    data_loader.load_dataset = mock_load_dataset_network_error
    
    try:
        with pytest.raises(RuntimeError) as exc_info:
            data_loader.fetch_locomo_dataset(subset=1)
        
        error_msg = str(exc_info.value)
        assert "Network" in error_msg or "fetch" in error_msg.lower()
        assert "fabrication" in error_msg.lower() or "halted" in error_msg.lower()
        
    finally:
        data_loader.load_dataset = original_load_dataset

def test_generate_noisy_graphs_with_empty_tasks():
    """Test that generating noisy graphs with an empty list returns an empty list."""
    tasks = []
    noisy_tasks = generate_noisy_graphs(tasks, noise_proportion=0.1, seed=42)
    assert len(noisy_tasks) == 0

def test_generate_noisy_graphs_single_task():
    """Test noisy graph generation with a single task."""
    tasks = [
        {
            "task_id": "single",
            "question": "Test?",
            "context": "A simple context.",
            "answer": "Answer"
        }
    ]
    
    noisy_tasks = generate_noisy_graphs(tasks, noise_proportion=0.2, seed=99)
    
    assert len(noisy_tasks) == 1
    assert noisy_tasks[0]["task_id"] == "single"
    assert "noisy_graph" in noisy_tasks[0]
    assert "original_graph" in noisy_tasks[0]