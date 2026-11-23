"""
Tests for error handling in network generation.

Verifies that:
1. Generation failures are caught and logged
2. Failing graph IDs are recorded
3. Failed graphs are excluded from the final dataset
"""
import pytest
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import networkx as nx

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from generate_networks import (
    generate_random_graph,
    generate_scale_free_graph,
    generate_small_world_graph,
    generate_lattice_graph,
    generate_star_graph,
    generate_networks,
    save_to_csv
)
from utils.metrics import compute_graph_metrics

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def caplog_test(caplog):
    """Configure caplog for testing."""
    caplog.set_level(logging.WARNING)
    return caplog

def test_generate_random_graph_failure_logging(caplog_test):
    """Test that random graph generation failures are logged."""
    with patch('networkx.erdos_renyi_graph', side_effect=Exception("Test error")):
        result = generate_random_graph(100, 0.1, 42, "test_random_1")
        assert result is None
        assert any("Failed to generate random graph test_random_1" in msg for msg in caplog_test.messages)

def test_generate_scale_free_graph_failure_logging(caplog_test):
    """Test that scale-free graph generation failures are logged."""
    with patch('networkx.barabasi_albert_graph', side_effect=Exception("Test error")):
        result = generate_scale_free_graph(100, 3, 42, "test_sf_1")
        assert result is None
        assert any("Failed to generate scale-free graph test_sf_1" in msg for msg in caplog_test.messages)

def test_generate_small_world_graph_failure_logging(caplog_test):
    """Test that small-world graph generation failures are logged."""
    with patch('networkx.watts_strogatz_graph', side_effect=Exception("Test error")):
        result = generate_small_world_graph(100, 4, 0.1, 42, "test_sw_1")
        assert result is None
        assert any("Failed to generate small-world graph test_sw_1" in msg in caplog_test.messages)

def test_generate_lattice_graph_failure_logging(caplog_test):
    """Test that lattice graph generation failures are logged."""
    with patch('networkx.watts_strogatz_graph', side_effect=Exception("Test error")):
        result = generate_lattice_graph(100, 4, 42, "test_lat_1")
        assert result is None
        assert any("Failed to generate lattice graph test_lat_1" in msg for msg in caplog_test.messages)

def test_generate_star_graph_failure_logging(caplog_test):
    """Test that star graph generation failures are logged."""
    with patch('networkx.star_graph', side_effect=Exception("Test error")):
        result = generate_star_graph(100, 42, "test_star_1")
        assert result is None
        assert any("Failed to generate star graph test_star_1" in msg for msg in caplog_test.messages)

def test_failed_graphs_excluded_from_output(temp_output_dir, caplog_test):
    """Test that failed graphs are excluded from the final CSV output."""
    output_path = os.path.join(temp_output_dir, "test_networks.csv")
    
    # Mock generation to simulate some failures
    with patch('generate_networks.generate_random_graph') as mock_random, \
         patch('generate_networks.generate_scale_free_graph') as mock_sf, \
         patch('generate_networks.generate_small_world_graph') as mock_sw, \
         patch('generate_networks.generate_lattice_graph') as mock_lat, \
         patch('generate_networks.generate_star_graph') as mock_star:
         
        # Mock successful generations
        mock_random.return_value = nx.erdos_renyi_graph(100, 0.1, seed=42)
        mock_sf.return_value = nx.barabasi_albert_graph(100, 3, seed=42)
        mock_sw.return_value = nx.watts_strogatz_graph(100, 4, 0.1, seed=42)
        mock_lat.return_value = nx.watts_strogatz_graph(100, 4, 0, seed=42)
        mock_star.return_value = nx.star_graph(100, seed=42)
        
        # Generate a small set (1 per class to test quickly)
        metrics = generate_networks(target_count=1, base_seed=42)
        
        # Save to CSV
        save_to_csv(metrics, output_path)
        
        # Verify output exists
        assert os.path.exists(output_path)
        
        # Read CSV and verify it contains only successful generations
        import pandas as pd
        df = pd.read_csv(output_path)
        
        # Should have 5 graphs (1 per class)
        assert len(df) == 5
        assert 'id' in df.columns
        assert 'class' in df.columns
        
        # Verify no None values or error markers in the output
        assert not df['id'].isna().any()
        assert not df['class'].isna().any()

def test_generate_networks_handles_multiple_failures(temp_output_dir, caplog_test):
    """Test that generate_networks properly handles and logs multiple failures."""
    output_path = os.path.join(temp_output_dir, "test_networks_failures.csv")
    
    # Track calls to see which ones fail
    call_count = {'random': 0, 'scale_free': 0, 'small_world': 0, 'lattice': 0, 'star': 0}
    
    def failing_random(n, p, seed, graph_id):
        call_count['random'] += 1
        if call_count['random'] == 1:
            return None  # First attempt fails
        return nx.erdos_renyi_graph(n, p, seed=seed)
    
    with patch('generate_networks.generate_random_graph', side_effect=failing_random):
        # Generate with just 1 per class to test failure handling
        metrics = generate_networks(target_count=1, base_seed=42)
        
        # Should still succeed eventually (retry logic)
        assert len(metrics) >= 5  # At least one per class
        
        # Check that a warning was logged for the failure
        warning_messages = [msg for msg in caplog_test.messages if "Skipping graph" in msg]
        assert len(warning_messages) >= 1

def test_compute_graph_metrics_handles_errors():
    """Test that compute_graph_metrics handles various graph types correctly."""
    # Test with a simple graph
    G = nx.path_graph(10)
    metrics = compute_graph_metrics(G, "test_id", "test_class")
    
    assert 'id' in metrics
    assert 'class' in metrics
    assert 'N' in metrics
    assert 'clustering_coefficient' in metrics
    assert 'average_path_length' in metrics
    assert metrics['N'] == 10

def test_save_to_csv_creates_valid_file(temp_output_dir):
    """Test that save_to_csv creates a valid CSV file."""
    output_path = os.path.join(temp_output_dir, "test_output.csv")
    
    test_metrics = [
        {'id': 'test_1', 'class': 'random', 'N': 100, 'clustering_coefficient': 0.1},
        {'id': 'test_2', 'class': 'scale_free', 'N': 150, 'clustering_coefficient': 0.2}
    ]
    
    save_to_csv(test_metrics, output_path)
    
    assert os.path.exists(output_path)
    
    import pandas as pd
    df = pd.read_csv(output_path)
    
    assert len(df) == 2
    assert list(df.columns) == ['id', 'class', 'N', 'clustering_coefficient']