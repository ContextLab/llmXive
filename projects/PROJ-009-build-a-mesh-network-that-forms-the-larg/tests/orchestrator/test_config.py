"""
Tests for the configuration manager.
"""
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from orchestrator.config import ConfigManager, load_config
from orchestrator.models import PhysicalNode, NodeStatus


class TestConfigManager:
    """Test suite for ConfigManager class."""

    @pytest.fixture
    def valid_yaml_config(self):
        """Create a valid YAML configuration string."""
        return """
        nodes:
          - node_id: "node-001"
            hostname: "192.168.1.10"
            username: "researcher"
            hardware_spec:
              cpu_cores: 8
              memory_gb: 32
              gpu: "NVIDIA A100"
            status: "available"
          - node_id: "node-002"
            hostname: "192.168.1.11"
            username: "researcher"
            hardware_spec:
              cpu_cores: 16
              memory_gb: 64
              gpu: "None"
            status: "busy"

        network:
          default_latency_ms: 5.0
          default_bandwidth_mbps: 1000.0
          packet_loss_threshold: 0.02
          heartbeat_timeout_seconds: 30.0
          max_retries: 3
          ssh_port: 22
          ssh_timeout_seconds: 10.0

        granularity:
          fine_chunk_size: 100
          medium_chunk_size: 1000
          coarse_chunk_size: 10000
          default_granularity: "medium"

        orchestrator:
          run_id: "test-run-001"
          data_dir: "data"
          log_dir: "data/raw"
          output_dir: "data/processed"
          max_concurrent_nodes: 5
          hard_timeout_hours: 4.0
          straggler_timeout_multiplier: 2.0
        """

    @pytest.fixture
    def temp_config_file(self, valid_yaml_config):
        """Create a temporary YAML config file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(valid_yaml_config)
            f.flush()
            yield f.name
        os.unlink(f.name)

    def test_load_valid_config(self, temp_config_file):
        """Test loading a valid configuration file."""
        manager = ConfigManager(temp_config_file)
        config = manager.load()

        assert config is not None
        assert len(config.nodes) == 2
        assert config.nodes[0].node_id == "node-001"
        assert config.nodes[1].node_id == "node-002"
        assert config.network.default_latency_ms == 5.0
        assert config.granularity.default_granularity == "medium"
        assert config.orchestrator.run_id == "test-run-001"
        assert config.orchestrator.hard_timeout_hours == 4.0

    def test_get_node_by_id(self, temp_config_file):
        """Test retrieving a specific node by ID."""
        manager = ConfigManager(temp_config_file)
        config = manager.load()

        node = config.get_node("node-001")
        assert node is not None
        assert node.node_id == "node-001"
        assert node.hostname == "192.168.1.10"

        node = config.get_node("non-existent")
        assert node is None

    def test_get_available_nodes(self, temp_config_file):
        """Test filtering available nodes."""
        manager = ConfigManager(temp_config_file)
        config = manager.load()

        available = config.get_available_nodes()
        assert len(available) == 1
        assert available[0].node_id == "node-001"

    def test_get_chunk_size_fine(self, temp_config_file):
        """Test getting fine granularity chunk size."""
        manager = ConfigManager(temp_config_file)
        config = manager.load()

        size = config.granularity.get_chunk_size("fine")
        assert size == 100

    def test_get_chunk_size_medium(self, temp_config_file):
        """Test getting medium granularity chunk size."""
        manager = ConfigManager(temp_config_file)
        config = manager.load()

        size = config.granularity.get_chunk_size("medium")
        assert size == 1000

    def test_get_chunk_size_coarse(self, temp_config_file):
        """Test getting coarse granularity chunk size."""
        manager = ConfigManager(temp_config_file)
        config = manager.load()

        size = config.granularity.get_chunk_size("coarse")
        assert size == 10000

    def test_get_chunk_size_default(self, temp_config_file):
        """Test getting default granularity chunk size."""
        manager = ConfigManager(temp_config_file)
        config = manager.load()

        size = config.granularity.get_chunk_size()
        assert size == 1000

    def test_get_chunk_size_invalid(self, temp_config_file):
        """Test error on invalid granularity level."""
        manager = ConfigManager(temp_config_file)
        config = manager.load()

        with pytest.raises(ValueError, match="Unknown granularity level"):
            config.granularity.get_chunk_size("invalid")

    def test_missing_config_file(self):
        """Test error when config file is missing."""
        manager = ConfigManager("non-existent/path/config.yaml")
        with pytest.raises(FileNotFoundError):
            manager.load()

    def test_empty_yaml_file(self):
        """Test error on empty YAML file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("")
            f.flush()
            temp_path = f.name

        try:
            manager = ConfigManager(temp_path)
            with pytest.raises(ValueError, match="empty or invalid"):
                manager.load()
        finally:
            os.unlink(temp_path)

    def test_get_config_before_load(self):
        """Test error when getting config before loading."""
        manager = ConfigManager()
        with pytest.raises(RuntimeError, match="not loaded"):
            manager.get_config()

    def test_reload_config(self, temp_config_file):
        """Test reloading configuration."""
        manager = ConfigManager(temp_config_file)
        config1 = manager.load()
        assert config1.orchestrator.run_id == "test-run-001"

        # Modify the file
        with open(temp_config_file, "r") as f:
            data = yaml.safe_load(f)

        data["orchestrator"]["run_id"] = "test-run-002"

        with open(temp_config_file, "w") as f:
            yaml.dump(data, f)

        config2 = manager.reload()
        assert config2.orchestrator.run_id == "test-run-002"


class TestLoadConfigFunction:
    """Test suite for the load_config convenience function."""

    def test_load_config_function(self, valid_yaml_config):
        """Test the load_config function."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(valid_yaml_config)
            f.flush()
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config is not None
            assert len(config.nodes) == 2
        finally:
            os.unlink(temp_path)

    def test_load_config_missing_file(self):
        """Test load_config with missing file."""
        with pytest.raises(FileNotFoundError):
            load_config("non-existent.yaml")
