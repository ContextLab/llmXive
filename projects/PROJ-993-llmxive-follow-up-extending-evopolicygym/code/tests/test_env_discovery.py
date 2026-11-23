import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from code.utils.env_discovery import discover_environments, write_discovered_envs, run_discovery
from utils.logging import get_logger

logger = get_logger(__name__)

class TestEnvDiscovery:
    @patch("code.utils.env_discovery.REGISTRY")
    def test_discover_zero_environments_raises(self, mock_registry):
        """Test that discovering 0 environments raises RuntimeError."""
        mock_registry.keys.return_value = []
        
        with pytest.raises(RuntimeError) as exc_info:
            discover_environments()
        
        assert "No environments found" in str(exc_info.value)

    @patch("code.utils.env_discovery.REGISTRY")
    def test_discover_fewer_than_16_warns(self, mock_registry, caplog):
        """Test that discovering < 16 environments logs a warning."""
        mock_registry.keys.return_value = ["env1", "env2"]
        
        with caplog.at_level(logging.WARNING):
            env_ids = discover_environments()
        
        assert len(env_ids) == 2
        assert "Expected 16 environments" in caplog.text

    @patch("code.utils.env_discovery.REGISTRY")
    def test_discover_exactly_16(self, mock_registry):
        """Test normal operation with exactly 16 environments."""
        mock_registry.keys.return_value = [f"env_{i}" for i in range(16)]
        
        env_ids = discover_environments()
        
        assert len(env_ids) == 16
        assert env_ids == [f"env_{i}" for i in range(16)]

    def test_write_discovered_envs_creates_files(self, tmp_path):
        """Test that write_discovered_envs creates JSON and log files."""
        env_ids = ["env1", "env2"]
        
        json_path = write_discovered_envs(env_ids, output_dir=str(tmp_path))
        
        # Check JSON file
        assert os.path.exists(json_path)
        with open(json_path, "r") as f:
            data = json.load(f)
        assert data == env_ids

        # Check log file
        log_path = str(tmp_path / "discovered_envs.log")
        assert os.path.exists(log_path)
        with open(log_path, "r") as f:
            content = f.read()
        assert "Discovered 2 environments" in content

    @patch("code.utils.env_discovery.discover_environments")
    @patch("code.utils.env_discovery.write_discovered_envs")
    def test_run_discovery_orchestrates(self, mock_write, mock_discover):
        """Test that run_discovery calls discover and write."""
        mock_discover.return_value = ["env1"]
        
        result = run_discovery()
        
        mock_discover.assert_called_once()
        mock_write.assert_called_once_with(["env1"])
        assert result == ["env1"]