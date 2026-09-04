"""
Unit tests for the experiment runner logic.
"""
import pytest
from unittest.mock import MagicMock, patch

from experiment_runner import run_single_experiment, GRANULARITY_OPTIONS, EXPRESSIVENESS_OPTIONS

def test_parameter_combinations():
    """Verify that all required parameter combinations are defined."""
    assert "coarse" in GRANULARITY_OPTIONS
    assert "fine" in GRANULARITY_OPTIONS
    assert "spatial" in EXPRESSIVENESS_OPTIONS
    assert "spatial+temporal" in EXPRESSIVENESS_OPTIONS

@patch("experiment_runner.load_traces_as_list")
@patch("experiment_runner.SymbolicGraphBuilder")
def test_run_single_experiment_success(mock_builder_class, mock_load_traces):
    """Test that run_single_experiment returns correct metrics dict on success."""
    # Setup mocks
    mock_builder = MagicMock()
    mock_builder_class.return_value = mock_builder
    
    # Mock a graph with specific node/edge counts
    mock_graph = MagicMock()
    mock_graph.number_of_nodes.return_value = 10
    mock_graph.number_of_edges.return_value = 5
    mock_builder.build_graph_from_trace.return_value = mock_graph
    
    mock_load_traces.return_value = [{"id": 1}, {"id": 2}] # 2 traces
    
    # Run
    result = run_single_experiment("coarse", "spatial", max_traces=2)
    
    # Assert
    assert result["granularity"] == "coarse"
    assert result["expressiveness"] == "spatial"
    assert result["traces_processed"] == 2
    assert result["avg_nodes"] == 10.0
    assert result["avg_edges"] == 5.0
    assert result["status"] == "success"

@patch("experiment_runner.load_traces_as_list")
def test_run_single_experiment_no_traces(mock_load_traces):
    """Test that run_single_experiment raises error if no traces loaded."""
    mock_load_traces.return_value = []
    
    with pytest.raises(RuntimeError, match="Failed to load any traces"):
        run_single_experiment("coarse", "spatial", max_traces=0)