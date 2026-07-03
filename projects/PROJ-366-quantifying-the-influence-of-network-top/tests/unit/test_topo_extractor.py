"""
Unit tests for topology_extractor.py (T021)
"""
import json
import os
import tempfile
from pathlib import Path
import pickle

import numpy as np
import networkx as nx
import pytest

# Import the module under test
from code.metrics.topology_extractor import (
    compute_local_clustering_coefficient,
    compute_shortest_path_stats,
    extract_metrics_for_graph,
    process_graph_file
)

def test_compute_local_clustering_coefficient():
    """Test clustering coefficient on a simple graph."""
    # Triangle: 3 nodes, all connected. Clustering should be 1.0
    G = nx.complete_graph(3)
    assert compute_local_clustering_coefficient(G, 0) == 1.0

    # Line: 1-2-3. Node 2 has 2 neighbors, 0 edges between them. Clustering = 0.
    G = nx.path_graph(3)
    assert compute_local_clustering_coefficient(G, 1) == 0.0

    # Isolated node: Clustering is 0 by definition (or NaN, networkx returns 0)
    G = nx.Graph()
    G.add_node(0)
    assert compute_local_clustering_coefficient(G, 0) == 0.0

def test_compute_shortest_path_stats():
    """Test shortest path stats calculation."""
    G = nx.star_graph(4) # Center 0, leaves 1,2,3,4
    
    # From center (0): distance to all leaves is 1.
    stats = compute_shortest_path_stats(G, 0)
    assert stats['mean'] == 1.0
    assert stats['max'] == 1.0
    assert stats['count'] == 4

    # From a leaf (1): distance to center is 1, to other leaves is 2.
    stats = compute_shortest_path_stats(G, 1)
    # Neighbors: 0 (dist 1), 2 (dist 2), 3 (dist 2), 4 (dist 2)
    assert stats['mean'] == pytest.approx(1.75) # (1+2+2+2)/4
    assert stats['max'] == 2.0
    assert stats['count'] == 4

def test_extract_metrics_for_graph():
    """Test full metric extraction."""
    G = nx.karate_club_graph()
    metrics = extract_metrics_for_graph(G)
    
    assert len(metrics) == G.number_of_nodes()
    
    # Check structure of one entry
    entry = metrics[0]
    assert 'node_id' in entry
    assert 'degree' in entry
    assert 'clustering_coefficient' in entry
    assert 'shortest_path_stats' in entry
    assert 'mean' in entry['shortest_path_stats']
    assert 'max' in entry['shortest_path_stats']
    assert 'count' in entry['shortest_path_stats']

def test_process_graph_file(tmp_path):
    """Test processing a graph file and saving metrics."""
    # Create a dummy graph
    G = nx.barbell_graph(5, 2)
    
    # Prepare input structure (simulating graph_builder output)
    graph_data = {
        'graph': G,
        'metadata': {'source': 'test'}
    }
    
    input_file = tmp_path / "test_graph.pkl"
    with open(input_file, 'wb') as f:
        pickle.dump(graph_data, f)
    
    output_dir = tmp_path / "metrics"
    output_dir.mkdir()
    
    out_path, global_stats = process_graph_file(input_file, output_dir)
    
    # Verify output file exists
    assert out_path.exists()
    
    # Verify content
    with open(out_path, 'r') as f:
        data = json.load(f)
    
    assert 'global_stats' in data
    assert 'node_metrics' in data
    assert data['global_stats']['num_nodes'] == G.number_of_nodes()
    assert data['global_stats']['num_edges'] == G.number_of_edges()
    
    # Verify global stats keys
    assert 'mean_degree' in data['global_stats']
    assert 'diameter' in data['global_stats']