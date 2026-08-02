"""
Unit tests for the Parameter Sweep Runner.

These tests verify that the SweepRunner correctly iterates over configurations,
handles different granularity settings, and produces valid result structures.
"""
import pytest
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from orchestrator.sweep_runner import SweepRunner, SweepConfig, generate_default_configs
from orchestrator.config import ConfigManager
from orchestrator.node_manager import NodeManager


class TestSweepConfig:
    """Tests for the SweepConfig dataclass."""

    def test_config_creation(self):
        """Test that a SweepConfig is created with correct defaults."""
        config = SweepConfig(
            run_id="test_001",
            granularity="medium",
            node_count=5,
            latency_ms=20,
            packet_loss_pct=0.5
        )
        
        assert config.run_id == "test_001"
        assert config.granularity == "medium"
        assert config.node_count == 5
        assert config.latency_ms == 20
        assert config.packet_loss_pct == 0.5
        assert config.start_time is not None


class TestGenerateDefaultConfigs:
    """Tests for the configuration generator."""

    def test_generate_creates_expected_count(self):
        """Verify the default grid size (3 granularities * 3 node counts * 3 latencies)."""
        configs = generate_default_configs()
        expected_count = 3 * 3 * 3 # 27
        assert len(configs) == expected_count

    def test_generate_covers_granularities(self):
        """Verify all granularity levels are present."""
        configs = generate_default_configs()
        granularities = {c.granularity for c in configs}
        assert granularities == {"fine", "medium", "coarse"}

    def test_generate_covers_node_counts(self):
        """Verify expected node counts are present."""
        configs = generate_default_configs()
        node_counts = {c.node_count for c in configs}
        assert node_counts == {3, 5, 8}

    def test_generate_covers_latencies(self):
        """Verify expected latency levels are present."""
        configs = generate_default_configs()
        latencies = {c.latency_ms for c in configs}
        assert latencies == {10, 50, 100}


class TestSweepRunner:
    """Tests for the SweepRunner class logic."""

    @pytest.fixture
    def mock_config_manager(self):
        """Provide a mock ConfigManager."""
        return MagicMock(spec=ConfigManager)

    @pytest.fixture
    def mock_node_manager(self):
        """Provide a mock NodeManager with available nodes."""
        mock_nodes = [MagicMock(node_id=f"node_{i}") for i in range(10)]
        manager = MagicMock(spec=NodeManager)
        manager.get_available_nodes.return_value = mock_nodes
        return manager

    def test_runner_initialization(self, mock_config_manager, mock_node_manager):
        """Test that SweepRunner initializes correctly."""
        runner = SweepRunner(mock_config_manager, mock_node_manager)
        assert runner.config_manager == mock_config_manager
        assert runner.node_manager == mock_node_manager
        assert len(runner.results) == 0

    def test_run_single_configuration_success(self, mock_config_manager, mock_node_manager):
        """Test a single successful configuration run."""
        runner = SweepRunner(mock_config_manager, mock_node_manager)
        config = SweepConfig(
            run_id="unit_test_1",
            granularity="medium",
            node_count=3,
            latency_ms=10,
            packet_loss_pct=0.0
        )

        # Mock the internal methods to avoid actual execution time
        with patch.object(runner, '_apply_network_impairments'):
            with patch('time.sleep', return_value=None): # Skip real sleep
                result = runner._run_single_configuration(config)

        assert result.config.run_id == "unit_test_1"
        assert result.status == "success"
        assert result.throughput_tasks_per_sec > 0
        assert result.coordination_overhead_ratio >= 0
        assert result.error_message is None

    def test_run_single_configuration_no_nodes(self, mock_config_manager, mock_node_manager):
        """Test failure when no nodes are available."""
        runner = SweepRunner(mock_config_manager, mock_node_manager)
        config = SweepConfig(
            run_id="unit_test_2",
            granularity="coarse",
            node_count=100, # Request more than available
            latency_ms=10,
            packet_loss_pct=0.0
        )
        
        # Mock get_available_nodes to return empty list
        mock_node_manager.get_available_nodes.return_value = []

        with patch('time.sleep', return_value=None):
            result = runner._run_single_configuration(config)

        assert result.status == "failed"
        assert "No available nodes" in (result.error_message or "")

    def test_export_results_creates_file(self, mock_config_manager, mock_node_manager):
        """Test that export_results creates a valid JSON file."""
        runner = SweepRunner(mock_config_manager, mock_node_manager)
        
        # Add a dummy result manually
        from orchestrator.sweep_runner import SweepResult
        dummy_config = SweepConfig(
            run_id="dummy",
            granularity="fine",
            node_count=1,
            latency_ms=0,
            packet_loss_pct=0.0
        )
        runner.results.append(SweepResult(
            config=dummy_config,
            status="success",
            throughput_tasks_per_sec=10.5,
            coordination_overhead_ratio=0.1,
            total_duration_sec=100.0
        ))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_sweep.json")
            runner.export_results(output_path)

            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]['run_id'] == 'dummy'
            assert data[0]['throughput_tasks_per_sec'] == 10.5

    def test_run_sweep_iterates_all_configs(self, mock_config_manager, mock_node_manager):
        """Test that run_sweep processes all provided configurations."""
        runner = SweepRunner(mock_config_manager, mock_node_manager)
        configs = [
            SweepConfig("c1", "fine", 2, 10, 0.0),
            SweepConfig("c2", "coarse", 4, 50, 0.0)
        ]

        with patch.object(runner, '_run_single_configuration') as mock_run:
            mock_run.side_effect = [
                SweepResult(configs[0], "success", 1.0, 0.1, 10.0),
                SweepResult(configs[1], "success", 2.0, 0.2, 20.0)
            ]
            
            results = runner.run_sweep(configs)

        assert len(results) == 2
        assert mock_run.call_count == 2
        assert runner.results == results