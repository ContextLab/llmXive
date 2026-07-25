import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import networkx as nx
import numpy as np

from code.src.generators.batch_runner import generate_batch, REJECTION_THRESHOLD
from code.src.utils.config import load_config

@pytest.fixture
def mock_config(tmp_path):
    """Create a minimal config file for testing."""
    config_data = {
        "global_seed": 42,
        "topology_targets": {
            "erdos_renyi": {"n": 10, "p": 0.3},
            "watts_strogatz": {"n": 10, "k": 4, "p": 0.1},
            "barabasi_albert": {"n": 10, "m": 2}
        },
        "generator": {
            "max_retry_attempts": 5,
            "sample_size_adjustment_factor": 1.5
        },
        "simulation": {
            "simulation_timeout_seconds": 300
        }
    }
    config_file = tmp_path / "config.yaml"
    import yaml
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    return config_data

@patch('code.src.generators.batch_runner.get_generator')
@patch('code.src.generators.batch_runner.save_graph_metadata')
@patch('code.src.generators.batch_runner.extract_all_metrics')
@patch('code.src.generators.batch_runner.get_run_log')
@patch('code.src.generators.batch_runner.ensure_data_directory')
def test_sample_size_adjustment_logic(
    mock_ensure_dir,
    mock_get_run_log,
    mock_extract_metrics,
    mock_save_meta,
    mock_get_gen,
    mock_config,
    tmp_path
):
    """
    Test that if the rejection rate exceeds 40%, the batch size is increased
    and an adjustment log entry is created.
    """
    # Setup mocks
    mock_run_log = {"adjustments": []}
    mock_get_run_log.return_value = mock_run_log
    mock_extract_metrics.return_value = {"clustering": 0.5, "avg_path": 2.0}
    
    # Mock a generator that fails the first 3 times then succeeds
    # Total attempts: 3 failures + 1 success = 4 attempts.
    # Rejection rate = 3/4 = 0.75 (> 0.40) -> Should trigger adjustment.
    # However, we need to simulate the loop logic carefully.
    # To trigger the adjustment, we need a high failure rate early on.
    # Let's mock the generator to return None (failure) for N times, then a graph.
    
    call_count = 0
    def mock_gen_factory(*args, **kwargs):
        gen = MagicMock()
        def side_effect():
            nonlocal call_count
            call_count += 1
            # Fail first 4 attempts to ensure high rejection rate
            if call_count <= 4:
                return None # Will cause retry loop to continue in generate_single_graph
            else:
                g = nx.erdos_renyi_graph(10, 0.3)
                return g
        gen.generate = side_effect
        return gen
    
    mock_get_gen.side_effect = mock_gen_factory

    # Run batch with target 1
    # We expect the loop to run until it gets 1 success, but with high failure rate,
    # the adjustment logic should trigger.
    # Note: The logic in generate_batch checks rejection rate after every attempt.
    
    # We need to patch `generate_single_graph` to simulate the specific failure/success pattern
    # more directly to ensure the threshold is hit.
    from code.src.generators import batch_runner
    
    original_gen_single = batch_runner.generate_single_graph
    
    attempt_log = []
    def mock_generate_single(generator, graph_id, topology_class, config):
        nonlocal call_count
        call_count += 1
        attempt_log.append(graph_id)
        
        # Simulate failure for first 4 attempts, then success
        if len(attempt_log) <= 4:
            return None, False
        else:
            g = nx.erdos_renyi_graph(10, 0.3)
            return g, True

    with patch.object(batch_runner, 'generate_single_graph', side_effect=mock_generate_single):
        with patch.object(batch_runner, 'get_generator', side_effect=mock_gen_factory):
            # Run with target 1
            result = generate_batch("erdos_renyi", target_count=1, config=mock_config, batch_id="test_batch")
    
    # Verify adjustment was triggered
    assert result["adjustment_applied"] is True
    assert "adjustment_details" in result
    assert result["adjustment_details"]["event"] == "SAMPLE_SIZE_ADJUSTMENT"
    assert result["adjustment_details"]["rejection_rate_at_trigger"] > REJECTION_THRESHOLD

@patch('code.src.generators.batch_runner.get_generator')
@patch('code.src.generators.batch_runner.save_graph_metadata')
@patch('code.src.generators.batch_runner.extract_all_metrics')
@patch('code.src.generators.batch_runner.get_run_log')
@patch('code.src.generators.batch_runner.ensure_data_directory')
def test_no_adjustment_on_low_rejection(
    mock_ensure_dir,
    mock_get_run_log,
    mock_extract_metrics,
    mock_save_meta,
    mock_get_gen,
    mock_config,
    tmp_path
):
    """
    Test that if rejection rate is low (< 40%), no adjustment is made.
    """
    mock_run_log = {"adjustments": []}
    mock_get_run_log.return_value = mock_run_log
    mock_extract_metrics.return_value = {"clustering": 0.5}
    
    def mock_gen_factory(*args, **kwargs):
        gen = MagicMock()
        g = nx.erdos_renyi_graph(10, 0.3)
        gen.generate = lambda: g
        return gen
    
    mock_get_gen.side_effect = mock_gen_factory
    
    # Run batch
    result = generate_batch("erdos_renyi", target_count=2, config=mock_config, batch_id="test_batch_2")
    
    # Verify no adjustment
    assert result["adjustment_applied"] is False
    assert result["rejection_rate"] < REJECTION_THRESHOLD