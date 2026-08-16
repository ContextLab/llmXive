import json
import os
import pickle
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from ingest.node_degree_stats_generator import (
    load_graphs,
    calculate_global_degree_distribution,
    compute_mode_and_stats,
    validate_mode_for_amorphous_silicon,
    main
)
from config import get_config

@pytest.fixture
def temp_graph_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create a mock graph
        graph1 = {
            "graph_id": "sample_01",
            "nodes": [
                {"id": 0, "degree": 4, "coords": [0.0, 0.0, 0.0]},
                {"id": 1, "degree": 4, "coords": [1.0, 0.0, 0.0]},
                {"id": 2, "degree": 3, "coords": [0.0, 1.0, 0.0]},
                {"id": 3, "degree": 5, "coords": [0.0, 0.0, 1.0]}
            ]
        }
        # Create another mock graph
        graph2 = {
            "graph_id": "sample_02",
            "nodes": [
                {"id": 0, "degree": 4, "coords": [0.0, 0.0, 0.0]},
                {"id": 1, "degree": 4, "coords": [1.0, 0.0, 0.0]},
                {"id": 2, "degree": 4, "coords": [0.0, 1.0, 0.0]}
            ]
        }
        
        with open(tmp_path / "graph_01.pkl", 'wb') as f:
            pickle.dump(graph1, f)
        with open(tmp_path / "graph_02.pkl", 'wb') as f:
            pickle.dump(graph2, f)
        
        yield tmp_path

def test_load_graphs(temp_graph_dir):
    graphs = load_graphs(temp_graph_dir)
    assert len(graphs) == 2
    assert graphs[0]['graph_id'] == 'sample_01'
    assert graphs[1]['graph_id'] == 'sample_02'

def test_calculate_global_degree_distribution(temp_graph_dir):
    graphs = load_graphs(temp_graph_dir)
    dist = calculate_global_degree_distribution(graphs)
    # Expected: 3 appears once, 4 appears 5 times, 5 appears once
    assert dist[3] == 1
    assert dist[4] == 5
    assert dist[5] == 1

def test_compute_mode_and_stats(temp_graph_dir):
    graphs = load_graphs(temp_graph_dir)
    dist = calculate_global_degree_distribution(graphs)
    stats = compute_mode_and_stats(dist)
    
    assert stats['mode'] == 4
    assert stats['mode_frequency'] == 5
    assert stats['total_nodes'] == 7
    # Mean: (3*1 + 4*5 + 5*1) / 7 = (3 + 20 + 5) / 7 = 28/7 = 4.0
    assert stats['mean_degree'] == 4.0

def test_validate_mode_for_amorphous_silicon():
    config = get_config()
    # Valid range
    assert validate_mode_for_amorphous_silicon(4, config) is True
    # Invalid range (too low)
    assert validate_mode_for_amorphous_silicon(2, config) is False
    # Invalid range (too high)
    assert validate_mode_for_amorphous_silicon(6, config) is False

def test_main_execution(temp_graph_dir, tmp_path):
    # Mock paths to point to our temp dir and a temp output
    mock_paths = {
        'processed_graphs': temp_graph_dir,
        'node_degree_stats': tmp_path / "node_degree_stats.json"
    }
    
    with mock.patch('ingest.node_degree_stats_generator.get_paths', return_value=mock_paths):
        main()
    
    assert mock_paths['node_degree_stats'].exists()
    
    with open(mock_paths['node_degree_stats'], 'r') as f:
        data = json.load(f)
    
    assert 'stats' in data
    assert data['stats']['mode'] == 4
    assert 'distribution' in data['stats']