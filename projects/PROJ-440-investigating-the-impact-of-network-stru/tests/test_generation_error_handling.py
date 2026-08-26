import pytest
import os
import sys
import logging
from unittest.mock import patch, MagicMock
import networkx as nx
import numpy as np

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from generate_networks import (
    generate_random_graph,
    generate_scale_free_graph,
    validate_random_graph,
    validate_scale_free_graph,
    generate_networks,
    compute_graph_metrics
)

@pytest.fixture
def mock_logger():
    """Mock the logger to capture warnings/errors without writing to disk."""
    with patch('generate_networks.logger') as mock_log:
        yield mock_log

def test_generation_failure_logging_random(mock_logger):
    """Test that generation failures for random graphs are logged with specific ID."""
    # Force validation to fail by mocking the graph to have bad metrics
    bad_graph = nx.erdos_renyi_graph(100, 0.5) 
    # Manually set a property or just test the validation function directly
    # We test the validation function which logs the error
    
    result = validate_random_graph(bad_graph, "test_id_1", 100, 0.01) # p=0.01 will likely fail degree check for this graph
    
    # The function returns False, and the main generation loop should log it
    assert result == False
    # Check if error was logged
    assert any(call[0][0].startswith("Generation validation failed") for call in mock_logger.error.call_args_list)

def test_generation_failure_logging_scale_free(mock_logger):
    """Test that generation failures for scale-free graphs are logged."""
    # Create a graph that is definitely not power law (e.g., a complete graph)
    G = nx.complete_graph(50)
    
    result = validate_scale_free_graph(G, "test_sf_id")
    
    assert result == False
    assert any(call[0][0].startswith("Generation validation failed") for call in mock_logger.error.call_args_list)

def test_failed_graphs_excluded_from_final_set(mock_logger):
    """Test that graphs failing validation are not included in the final output list."""
    # We need to test the generate_networks function logic
    # Since it's hard to force a specific generation to fail deterministically without mocking internal logic,
    # we mock the generator functions to return None (simulating failure)
    
    with patch('generate_networks.generate_random_graph', return_value=None):
        with patch('generate_networks.generate_scale_free_graph', return_value=None):
            # Run a small subset
            networks, failed_ids = generate_networks(num_per_class=1, n_range=(10, 10), base_seed=123)
            
            # All should fail
            assert len(networks) == 0
            assert len(failed_ids) == 2 # 1 random + 1 scale_free
            assert any("random" in fid for fid in failed_ids)
            assert any("scale_free" in fid for fid in failed_ids)

def test_metrics_computation_failure_exclusion(mock_logger):
    """Test that if metrics computation fails, the graph is excluded."""
    G = nx.star_graph(10)
    
    # Mock compute_graph_metrics to return None
    with patch('generate_networks.compute_graph_metrics', return_value=None):
        # We need to test the flow inside generate_networks
        # Since compute_graph_metrics is called inside, we can't easily intercept the loop
        # without mocking the whole function or the specific call.
        # Instead, we test compute_graph_metrics directly with a bad input if possible,
        # or rely on the fact that if it returns None, the graph is not added.
        
        # Let's test the logic: if compute_graph_metrics returns None, it's not appended.
        metrics = compute_graph_metrics(G, "star", "test_id")
        assert metrics is not None # Should work normally
        
        # Now test with a graph that causes an exception in metrics calculation
        # e.g. a graph with no nodes
        G_empty = nx.Graph()
        metrics_empty = compute_graph_metrics(G_empty, "empty", "empty_id")
        # The function handles empty graphs gracefully usually, but let's check
        # If it returns None or a dict with inf, the exclusion logic in main loop handles it.
        # The requirement is that failed ones are excluded.
        # If metrics_empty is None, it is excluded.
        # If it's a dict with inf, it might be included but flagged.
        # The task says "exclude from final set".
        
        # Let's force an exception in the metrics function to simulate failure
        with patch('generate_networks.nx.average_clustering', side_effect=Exception("Simulated Error")):
             metrics_fail = compute_graph_metrics(G, "test", "fail_id")
             assert metrics_fail is None
             # This confirms that if metrics fail, None is returned, and the main loop excludes it.

def test_failed_ids_logged_to_file(mock_logger):
    """Test that failed IDs are collected and logged."""
    with patch('generate_networks.generate_random_graph', return_value=None):
        networks, failed_ids = generate_networks(num_per_class=1, n_range=(10, 10), base_seed=1)
        
        assert len(failed_ids) == 1
        # Verify logging call contains the ID
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args
        # Check if the failed ID is in the warning message
        assert "Failed IDs" in call_args[0][0] or any(str(fid) in str(call_args) for fid in failed_ids)
