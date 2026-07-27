import pytest
import pandas as pd
import json
import os
from pathlib import Path
from unittest.mock import patch

from metrics import process_batch, load_graph_from_json

@pytest.fixture
def sample_graphs_dir(tmp_path):
    """Create a directory with sample graph JSON files."""
    graphs_dir = tmp_path / "graphs"
    graphs_dir.mkdir()
    
    # Graph 1: 3 nodes, 2 edges (linear)
    graph1 = {
        'nodes': ['A', 'B', 'C'],
        'edges': [['A', 'B'], ['B', 'C']]
    }
    with open(graphs_dir / "trajectory_1.json", 'w') as f:
        json.dump(graph1, f)
    
    # Graph 2: 4 nodes, 3 edges (linear)
    graph2 = {
        'nodes': ['A', 'B', 'C', 'D'],
        'edges': [['A', 'B'], ['B', 'C'], ['C', 'D']]
    }
    with open(graphs_dir / "trajectory_2.json", 'w') as f:
        json.dump(graph2, f)
    
    # Graph 3: 4 nodes, 4 edges (cycle)
    graph3 = {
        'nodes': ['A', 'B', 'C', 'D'],
        'edges': [['A', 'B'], ['B', 'C'], ['C', 'D'], ['D', 'A']]
    }
    with open(graphs_dir / "trajectory_3.json", 'w') as f:
        json.dump(graph3, f)
    
    return str(graphs_dir)

def test_process_batch_writes_csv(sample_graphs_dir, tmp_path):
    """Test that process_batch writes metrics.csv correctly."""
    output_csv = tmp_path / "metrics.csv"
    
    # Mock the trajectory ID extraction if needed, or assume filename mapping
    # In this test, we assume the function processes all JSON files in the directory
    process_batch(sample_graphs_dir, str(output_csv))
    
    assert output_csv.exists(), "metrics.csv not created"
    
    df = pd.read_csv(output_csv)
    assert 'trajectory_id' in df.columns
    assert 'global_connectivity' in df.columns
    assert 'avg_branching_factor' in df.columns
    
    # Should have 3 rows for 3 graphs
    assert len(df) == 3

def test_process_batch_handles_malformed_json(tmp_path):
    """Test that process_batch handles malformed JSON files gracefully."""
    graphs_dir = tmp_path / "graphs"
    graphs_dir.mkdir()
    
    # Create a valid graph
    graph1 = {'nodes': ['A'], 'edges': []}
    with open(graphs_dir / "valid.json", 'w') as f:
        json.dump(graph1, f)
    
    # Create a malformed JSON file
    malformed_path = graphs_dir / "malformed.json"
    with open(malformed_path, 'w') as f:
        f.write("{ this is not valid json }")
    
    output_csv = tmp_path / "metrics.csv"
    
    # Should not crash, but skip the malformed file
    process_batch(str(graphs_dir), str(output_csv))
    
    assert output_csv.exists()
    df = pd.read_csv(output_csv)
    # Only the valid graph should be processed
    assert len(df) == 1

def test_process_batch_zero_edge_graph(tmp_path):
    """Test that process_batch handles graphs with zero edges."""
    graphs_dir = tmp_path / "graphs"
    graphs_dir.mkdir()
    
    # Graph with nodes but no edges
    graph = {'nodes': ['A', 'B', 'C'], 'edges': []}
    with open(graphs_dir / "no_edges.json", 'w') as f:
        json.dump(graph, f)
    
    output_csv = tmp_path / "metrics.csv"
    process_batch(str(graphs_dir), str(output_csv))
    
    df = pd.read_csv(output_csv)
    assert len(df) == 1
    # Connectivity should be 0.0 for zero edges
    assert df.iloc[0]['global_connectivity'] == 0.0
    # Branching should be 0.0 for zero edges
    assert df.iloc[0]['avg_branching_factor'] == 0.0
