import pytest
import json
import os
import tempfile
from pathlib import Path
import networkx as nx
from metrics import load_graph_from_json, calculate_global_connectivity, calculate_avg_branching_factor, process_batch

def test_load_graph_from_json():
    """Test loading a graph from JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'nodes': [1, 2, 3], 'edges': [(1, 2), (2, 3)]}, f)
        temp_path = f.name
    
    try:
        G = load_graph_from_json(temp_path)
        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 2
    finally:
        os.unlink(temp_path)

def test_calculate_global_connectivity():
    """Test global connectivity calculation."""
    G = nx.DiGraph()
    G.add_nodes_from([1, 2, 3])
    G.add_edges_from([(1, 2), (2, 3)])
    
    # 2 edges / (3 * 2) = 2/6 = 0.333...
    expected = 2 / 6
    assert abs(calculate_global_connectivity(G) - expected) < 1e-6

def test_calculate_global_connectivity_zero_nodes():
    """Test global connectivity with zero nodes."""
    G = nx.DiGraph()
    assert calculate_global_connectivity(G) == 0.0

def test_calculate_avg_branching_factor():
    """Test average branching factor calculation."""
    G = nx.DiGraph()
    G.add_nodes_from([1, 2, 3])
    G.add_edges_from([(1, 2), (2, 3)])
    
    # Node 1: out-degree 1, Node 2: out-degree 1, Node 3: out-degree 0
    # Total out-degree = 2, N = 3, avg = 2/3
    expected = 2 / 3
    assert abs(calculate_avg_branching_factor(G) - expected) < 1e-6

def test_calculate_avg_branching_factor_zero_nodes():
    """Test average branching factor with zero nodes."""
    G = nx.DiGraph()
    assert calculate_avg_branching_factor(G) == 0.0

def test_process_batch():
    """Test batch processing of graphs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test graphs
        graph1 = nx.DiGraph()
        graph1.add_nodes_from([1, 2])
        graph1.add_edges_from([(1, 2)])
        
        graph2 = nx.DiGraph()
        graph2.add_nodes_from([1, 2, 3, 4])
        graph2.add_edges_from([(1, 2), (2, 3), (3, 4)])
        
        # Save graphs
        graph_path = Path(temp_dir)
        with open(graph_path / "trajectory_1.json", 'w') as f:
            json.dump({'nodes': list(graph1.nodes()), 'edges': list(graph1.edges())}, f)
        with open(graph_path / "trajectory_2.json", 'w') as f:
            json.dump({'nodes': list(graph2.nodes()), 'edges': list(graph2.edges())}, f)
        
        output_path = Path(temp_dir) / "metrics.csv"
        process_batch(temp_dir, str(output_path))
        
        # Verify output
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        # Check column names match spec
        assert 'trajectory_id' in rows[0]
        assert 'global_connectivity' in rows[0]
        assert 'avg_branching_factor' in rows[0]

import csv
