"""
Unit tests for data_loader.py
"""
import pytest
import json
import os
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import numpy as np

# Import the module under test
from data_loader import (
    generate_noisy_graph_dataset, 
    validate_graph, 
    get_graph_statistics,
    ensure_output_dirs,
    load_graphs
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)

@pytest.fixture
def sample_graph():
    """Create a sample graph for testing."""
    return {
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            {"source": "A", "target": "B", "relation": "rel1"},
            {"source": "B", "target": "C", "relation": "rel2"},
            {"source": "C", "target": "D", "relation": "rel3"},
            {"source": "A", "target": "C", "relation": "rel4"}
        ]
    }

def test_generate_noisy_graph_dataset_preserves_edge_count(temp_dir, sample_graph):
    """
    Test that generate_noisy_graph_dataset preserves the total edge count.
    """
    # Create input file
    input_path = temp_dir / "clean_graphs.json"
    with open(input_path, 'w') as f:
        json.dump({"task1": sample_graph}, f)
    
    output_path = temp_dir / "noisy_graphs.json"
    
    # Generate noisy graphs
    noisy_graphs = generate_noisy_graph_dataset(input_path, output_path, ratio=0.5, seed=42)
    
    # Verify output file exists and has content
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    # Verify edge count is preserved
    clean_edges = len(sample_graph["edges"])
    noisy_edges = len(noisy_graphs["task1"]["edges"])
    
    assert noisy_edges == clean_edges, f"Edge count changed from {clean_edges} to {noisy_edges}"

def test_generate_noisy_graph_dataset_no_self_loops(temp_dir, sample_graph):
    """Test that noisy graphs do not contain self-loops."""
    input_path = temp_dir / "clean_graphs.json"
    with open(input_path, 'w') as f:
        json.dump({"task1": sample_graph}, f)
    
    output_path = temp_dir / "noisy_graphs.json"
    
    noisy_graphs = generate_noisy_graph_dataset(input_path, output_path, ratio=1.0, seed=42)
    
    for edge in noisy_graphs["task1"]["edges"]:
        assert edge["source"] != edge["target"], f"Self-loop detected: {edge}"

def test_generate_noisy_graph_dataset_preserves_nodes(temp_dir, sample_graph):
    """Test that noisy graphs preserve the set of nodes."""
    input_path = temp_dir / "clean_graphs.json"
    with open(input_path, 'w') as f:
        json.dump({"task1": sample_graph}, f)
    
    output_path = temp_dir / "noisy_graphs.json"
    
    noisy_graphs = generate_noisy_graph_dataset(input_path, output_path, ratio=0.5, seed=42)
    
    original_nodes = set(sample_graph["nodes"])
    noisy_nodes = set(noisy_graphs["task1"]["nodes"])
    
    assert original_nodes == noisy_nodes, "Node set changed during noise injection"

def test_generate_noisy_graph_dataset_determinism(temp_dir, sample_graph):
    """Test that noise injection with the same seed is deterministic."""
    input_path = temp_dir / "clean_graphs.json"
    with open(input_path, 'w') as f:
        json.dump({"task1": sample_graph}, f)
    
    output_path1 = temp_dir / "noisy_graphs1.json"
    output_path2 = temp_dir / "noisy_graphs2.json"
    
    # Generate twice with same seed
    generate_noisy_graph_dataset(input_path, output_path1, ratio=0.5, seed=42)
    generate_noisy_graph_dataset(input_path, output_path2, ratio=0.5, seed=42)
    
    # Load and compare
    with open(output_path1, 'r') as f1, open(output_path2, 'r') as f2:
        noisy1 = json.load(f1)
        noisy2 = json.load(f2)
    
    assert json.dumps(noisy1, sort_keys=True) == json.dumps(noisy2, sort_keys=True)

def test_generate_noisy_graph_dataset_file_not_found(temp_dir):
    """Test that FileNotFoundError is raised when input file does not exist."""
    input_path = temp_dir / "nonexistent.json"
    output_path = temp_dir / "output.json"
    
    with pytest.raises(FileNotFoundError):
        generate_noisy_graph_dataset(input_path, output_path)

def test_generate_noisy_graph_dataset_empty_file(temp_dir):
    """Test that ValueError is raised when input file is empty."""
    input_path = temp_dir / "empty.json"
    output_path = temp_dir / "output.json"
    
    # Create empty file
    input_path.touch()
    
    with pytest.raises(ValueError):
        generate_noisy_graph_dataset(input_path, output_path)

def test_generate_noisy_graph_dataset_empty_graphs(temp_dir):
    """Test that ValueError is raised when input contains no graphs."""
    input_path = temp_dir / "empty_graphs.json"
    output_path = temp_dir / "output.json"
    
    with open(input_path, 'w') as f:
        json.dump({}, f)
    
    with pytest.raises(ValueError):
        generate_noisy_graph_dataset(input_path, output_path)

def test_generate_noisy_graph_dataset_single_node_graph(temp_dir):
    """Test handling of single-node graphs."""
    single_node_graph = {
        "nodes": ["A"],
        "edges": []
    }
    
    input_path = temp_dir / "clean_graphs.json"
    with open(input_path, 'w') as f:
        json.dump({"task1": single_node_graph}, f)
    
    output_path = temp_dir / "noisy_graphs.json"
    
    # Should not crash
    noisy_graphs = generate_noisy_graph_dataset(input_path, output_path, ratio=0.1, seed=42)
    
    assert noisy_graphs["task1"]["edges"] == []
    assert noisy_graphs["task1"]["nodes"] == ["A"]

def test_generate_noisy_graph_dataset_different_seeds_produce_different_results(temp_dir, sample_graph):
    """Test that different seeds produce different noisy graphs."""
    input_path = temp_dir / "clean_graphs.json"
    with open(input_path, 'w') as f:
        json.dump({"task1": sample_graph}, f)
    
    output_path1 = temp_dir / "noisy_graphs_seed42.json"
    output_path2 = temp_dir / "noisy_graphs_seed123.json"
    
    generate_noisy_graph_dataset(input_path, output_path1, ratio=0.5, seed=42)
    generate_noisy_graph_dataset(input_path, output_path2, ratio=0.5, seed=123)
    
    with open(output_path1, 'r') as f1, open(output_path2, 'r') as f2:
        noisy1 = json.load(f1)
        noisy2 = json.load(f2)
    
    # They should be different (with high probability)
    assert json.dumps(noisy1, sort_keys=True) != json.dumps(noisy2, sort_keys=True)

def test_generate_noisy_graph_dataset_output_file_created(temp_dir, sample_graph):
    """Test that the output file is created at the specified path."""
    input_path = temp_dir / "clean_graphs.json"
    with open(input_path, 'w') as f:
        json.dump({"task1": sample_graph}, f)
    
    output_path = temp_dir / "custom_output.json"
    
    generate_noisy_graph_dataset(input_path, output_path, ratio=0.1, seed=42)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0