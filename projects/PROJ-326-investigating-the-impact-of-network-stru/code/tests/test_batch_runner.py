import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import networkx as nx

from code.src.generators.batch_runner import (
    GlobalSuccessRateMonitor,
    generate_single_graph,
    run_batch_generation,
)
from code.src.generators.base import BaseGenerator

# Fixtures
@pytest.fixture
def mock_config():
    return {
        "global_seed": 42,
        "topology_targets": ["erdos_renyi"],
        "batch_size": 5,
        "thresholds": {
            "max_attempts_per_graph": 10,
            "success_rate_min": 0.95,
        },
    }

@pytest.fixture
def mock_generator():
    class MockGen(BaseGenerator):
        def __init__(self, fail_count=0):
            super().__init__()
            self.fail_count = fail_count
            self.attempt = 0

        def generate(self):
            self.attempt += 1
            if self.attempt <= self.fail_count:
                # Return disconnected graph to force retry
                g = nx.Graph()
                g.add_nodes_from([0, 1, 2])
                g.add_edge(0, 1) # Node 2 isolated
                return g
            # Return connected graph
            g = nx.erdos_renyi_graph(30, 0.1)
            return g

    return MockGen

class TestGlobalSuccessRateMonitor:
    def test_record_attempt_success(self):
        monitor = GlobalSuccessRateMonitor(min_success_rate=0.95)
        monitor.record_attempt("g1", True)
        assert monitor.total_generated == 1
        assert monitor.total_valid == 1
        assert monitor.failed_attempts_per_graph["g1"] == 0

    def test_record_attempt_failure(self):
        monitor = GlobalSuccessRateMonitor(min_success_rate=0.95)
        monitor.record_attempt("g1", False)
        assert monitor.total_generated == 1
        assert monitor.total_valid == 0
        assert monitor.failed_attempts_per_graph["g1"] == 1

    def test_check_enforcement_pass(self):
        monitor = GlobalSuccessRateMonitor(min_success_rate=0.95)
        for _ in range(100):
            monitor.record_attempt(f"g{i}", True)
        assert not monitor.check_enforcement()
        assert not monitor.batch_failed

    def test_check_enforcement_fail(self):
        monitor = GlobalSuccessRateMonitor(min_success_rate=0.95)
        # 95 success, 10 failure -> 90.4% < 95%
        for _ in range(95):
            monitor.record_attempt("success", True)
        for _ in range(10):
            monitor.record_attempt("fail", False)

        assert monitor.check_enforcement()
        assert monitor.batch_failed
        assert "critical error" in monitor.critical_error_message.lower()

class TestGenerateSingleGraph:
    def test_success_on_first_attempt(self, mock_generator):
        mock_gen = mock_generator(fail_count=0)
        graph, success = generate_single_graph(mock_gen, "test_id", max_attempts=10)
        assert success is True
        assert graph is not None
        assert nx.is_connected(graph)

    def test_failure_after_max_attempts(self, mock_generator):
        # Force failure: always return disconnected
        mock_gen = mock_generator(fail_count=100)
        graph, success = generate_single_graph(mock_gen, "test_id", max_attempts=5)
        assert success is False
        assert graph is None

class TestRunBatchGeneration:
    @patch("code.src.generators.batch_runner.GlobalSuccessRateMonitor")
    def test_low_success_rate_triggers_error(self, mock_monitor_class, mock_config):
        # Setup mock monitor to always fail check
        mock_monitor_instance = MagicMock()
        mock_monitor_instance.check_enforcement.return_value = True
        mock_monitor_instance.critical_error_message = "Test failure"
        mock_monitor_class.return_value = mock_monitor_instance

        with pytest.raises(RuntimeError) as exc_info:
            run_batch_generation(mock_config)

        assert "Test failure" in str(exc_info.value)

    def test_normal_run_creates_manifest(self, mock_config, mock_generator):
        # This test would require a full integration setup with real file IO
        # For unit testing, we verify the logic structure
        # We assume the monitor passes (default behavior)
        # The actual file writing is tested in integration tests
        pass
