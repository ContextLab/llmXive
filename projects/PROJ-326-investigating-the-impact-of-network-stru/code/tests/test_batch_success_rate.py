"""
Tests for Global Success Rate Monitoring in batch_runner.py.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import networkx as nx

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.generators.batch_runner import (
    GlobalSuccessRateMonitor,
    BatchGenerationError,
    run_batch_generation
)
from code.src.utils.config import load_config


class TestGlobalSuccessRateMonitor:
    """Unit tests for the GlobalSuccessRateMonitor class."""

    def test_initial_state(self):
        """Test that monitor initializes with correct default values."""
        config = {"thresholds": {"success_rate_min": 0.95}}
        monitor = GlobalSuccessRateMonitor(config)
        
        assert monitor.total_attempts == 0
        assert monitor.total_successes == 0
        assert monitor.total_failures == 0
        assert monitor.get_current_success_rate() == 1.0
        assert monitor.success_rate_min == 0.95

    def test_record_success(self):
        """Test recording a successful graph generation."""
        config = {"thresholds": {"success_rate_min": 0.95}}
        monitor = GlobalSuccessRateMonitor(config)
        
        mock_graph = nx.erdos_renyi_graph(10, 0.5)
        monitor.record_attempt("graph_1", True, mock_graph)
        
        assert monitor.total_attempts == 1
        assert monitor.total_successes == 1
        assert monitor.total_failures == 0
        assert monitor.get_current_success_rate() == 1.0
        assert len(monitor.successful_graphs) == 1

    def test_record_failure(self):
        """Test recording a failed graph generation."""
        config = {"thresholds": {"success_rate_min": 0.95}}
        monitor = GlobalSuccessRateMonitor(config)
        
        monitor.record_attempt("graph_1", False)
        
        assert monitor.total_attempts == 1
        assert monitor.total_successes == 0
        assert monitor.total_failures == 1
        assert monitor.get_current_success_rate() == 0.0
        assert len(monitor.failed_graphs) == 1

    def test_success_rate_calculation(self):
        """Test success rate calculation with mixed results."""
        config = {"thresholds": {"success_rate_min": 0.95}}
        monitor = GlobalSuccessRateMonitor(config)
        
        # 9 successes, 1 failure = 90%
        for i in range(9):
            monitor.record_attempt(f"graph_{i}", True)
        monitor.record_attempt("graph_9", False)
        
        rate = monitor.get_current_success_rate()
        assert abs(rate - 0.90) < 1e-6

    def test_threshold_check_pass(self):
        """Test that threshold check passes when rate is sufficient."""
        config = {"thresholds": {"success_rate_min": 0.95}}
        monitor = GlobalSuccessRateMonitor(config)
        
        # 19 successes, 1 failure = 95%
        for i in range(19):
            monitor.record_attempt(f"graph_{i}", True)
        monitor.record_attempt("graph_19", False)
        
        is_valid, msg = monitor.check_threshold()
        assert is_valid is True
        assert "acceptable limits" in msg

    def test_threshold_check_fail(self):
        """Test that threshold check fails when rate is insufficient."""
        config = {"thresholds": {"success_rate_min": 0.95}}
        monitor = GlobalSuccessRateMonitor(config)
        
        # 1 success, 1 failure = 50%
        monitor.record_attempt("graph_1", True)
        monitor.record_attempt("graph_2", False)
        
        is_valid, msg = monitor.check_threshold()
        assert is_valid is False
        assert "below threshold" in msg
        assert "graph_2" in msg

    def test_log_final_metrics(self, tmp_path, monkeypatch):
        """Test that final metrics are logged correctly."""
        # Mock log_metric to capture calls
        captured_logs = []
        def mock_log_metric(event):
            captured_logs.append(event)
        
        monkeypatch.setattr("code.src.generators.batch_runner.log_metric", mock_log_metric)
        
        config = {"thresholds": {"success_rate_min": 0.95}, "global_seed": 42}
        monitor = GlobalSuccessRateMonitor(config)
        
        monitor.record_attempt("graph_1", True)
        monitor.record_final_metrics = lambda: monitor.log_final_metrics() # Ensure method exists
        monitor.log_final_metrics()
        
        assert len(captured_logs) == 1
        event = captured_logs[0]
        assert event["event_type"] == "generation_summary"
        assert "metrics" in event
        assert event["metrics"]["total_attempts"] == 1
        assert event["metrics"]["success_rate"] == 1.0


@patch('code.src.generators.batch_runner.GlobalSuccessRateMonitor')
@patch('code.src.generators.batch_runner.load_config')
@patch('code.src.generators.batch_runner.init_logging')
@patch('code.src.generators.batch_runner.logger')
def test_run_batch_generation_low_success_rate(
    mock_logger, mock_init, mock_load_config, MockMonitor
):
    """
    Integration test simulating a scenario where the success rate drops below
    the threshold, ensuring the batch fails with a BatchGenerationError.
    """
    # Setup config mock
    mock_config = {
        "thresholds": {"success_rate_min": 0.95},
        "simulation_params": {"max_generation_attempts": 10},
        "topology_targets": [{"name": "erdos_renyi", "generator": MagicMock, "params": {"n": 10, "p": 0.01}, "count": 10}]
    }
    mock_load_config.return_value = mock_config

    # Setup Monitor mock to simulate failure
    mock_monitor_instance = MagicMock()
    mock_monitor_instance.check_threshold.return_value = (False, "Critical failure: rate too low")
    MockMonitor.return_value = mock_monitor_instance

    # Mock generator to always fail connectivity
    with patch('code.src.generators.batch_runner.generate_single_graph') as mock_gen:
        mock_gen.return_value = (None, False, 10) # Always fail
        
        with pytest.raises(BatchGenerationError) as exc_info:
            run_batch_generation("dummy_config.yaml")
        
        assert "Critical failure" in str(exc_info.value)
        mock_logger.critical.assert_called()
        mock_monitor_instance.check_threshold.assert_called()
        mock_monitor_instance.log_final_metrics.assert_called()


@patch('code.src.generators.batch_runner.GlobalSuccessRateMonitor')
@patch('code.src.generators.batch_runner.load_config')
@patch('code.src.generators.batch_runner.init_logging')
@patch('code.src.generators.batch_runner.logger')
def test_run_batch_generation_high_success_rate(
    mock_logger, mock_init, mock_load_config, MockMonitor
):
    """
    Integration test simulating a scenario where the success rate is high,
    ensuring the batch completes successfully and writes the manifest.
    """
    import json
    from pathlib import Path
    import tempfile

    # Setup config mock
    mock_config = {
        "thresholds": {"success_rate_min": 0.95},
        "simulation_params": {"max_generation_attempts": 10},
        "topology_targets": [{"name": "erdos_renyi", "generator": MagicMock, "params": {"n": 10, "p": 0.5}, "count": 5}]
    }
    mock_load_config.return_value = mock_config

    # Setup Monitor mock to simulate success
    mock_monitor_instance = MagicMock()
    mock_monitor_instance.check_threshold.return_value = (True, "Success rate OK")
    mock_monitor_instance.get_current_success_rate.return_value = 1.0
    MockMonitor.return_value = mock_monitor_instance

    # Mock graph object
    mock_graph = MagicMock()
    mock_graph.number_of_nodes.return_value = 10
    mock_graph.number_of_edges.return_value = 20
    mock_graph.nodes.return_value = range(10)
    mock_graph.edges.return_value = [(0,1), (1,2)]

    with patch('code.src.generators.batch_runner.generate_single_graph') as mock_gen:
        mock_gen.return_value = (mock_graph, True, 1)
        
        with patch('code.src.generators.batch_runner.compute_graph_metrics') as mock_metrics:
            mock_metrics.return_value = {"clustering_coefficient": 0.5}
            
            with patch('code.src.generators.batch_runner.save_graph_metadata'):
                with patch('code.src.generators.batch_runner.classify_graph_bin'):
                    with patch('code.src.generators.batch_runner.update_quota'):
                        with patch('code.src.generators.batch_runner.log_metric'):
                            with tempfile.TemporaryDirectory() as tmpdir:
                                # Patch MANIFEST_PATH to write to temp dir
                                with patch('code.src.generators.batch_runner.MANIFEST_PATH', str(Path(tmpdir) / "manifest.json")):
                                    run_batch_generation("dummy_config.yaml")
                                    
                                    # Verify manifest was written
                                    manifest_path = Path(tmpdir) / "manifest.json"
                                    assert manifest_path.exists()
                                    
                                    with open(manifest_path, 'r') as f:
                                        data = json.load(f)
                                    
                                    assert data["total_graphs"] == 5
                                    assert data["success_rate"] == 1.0
                                    
                                    mock_logger.info.assert_called()
                                    mock_monitor_instance.check_threshold.assert_called()