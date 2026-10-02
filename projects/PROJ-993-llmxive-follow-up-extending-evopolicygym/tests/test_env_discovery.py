import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from utils.env_discovery import discover_environments, write_discovered_envs, run_discovery
from utils.logging import setup_logging

# Setup logging for tests
setup_logging(log_level="DEBUG")

class TestEnvDiscovery:
    @patch('utils.env_discovery.get_logger')
    @patch('utils.env_discovery.REGISTRY')
    def test_discover_environments_success(self, mock_registry, mock_logger):
        """Test successful discovery of environments."""
        mock_envs = {"env_1": MagicMock(), "env_2": MagicMock(), "env_3": MagicMock()}
        mock_registry.keys.return_value = mock_envs.keys()
        
        env_ids = discover_environments()
        
        assert len(env_ids) == 3
        assert "env_1" in env_ids
        assert "env_2" in env_ids
        assert "env_3" in env_ids
        
        mock_logger.assert_called()

    @patch('utils.env_discovery.get_logger')
    @patch('utils.env_discovery.REGISTRY')
    def test_discover_environments_empty(self, mock_registry, mock_logger):
        """Test that empty registry raises RuntimeError."""
        mock_registry.keys.return_value = []
        
        with pytest.raises(RuntimeError) as exc_info:
            discover_environments()
        
        assert "No environments found" in str(exc_info.value)

    @patch('utils.env_discovery.get_logger')
    def test_discover_environments_import_error(self, mock_logger):
        """Test that ImportError is handled correctly."""
        with patch.dict('sys.modules', {'evopolicygym.envs': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module")):
                with pytest.raises(RuntimeError) as exc_info:
                    discover_environments()
                
                assert "Cannot discover environments" in str(exc_info.value)

    @patch('utils.env_discovery.get_logger')
    @patch('utils.env_discovery.REGISTRY')
    def test_write_discovered_envs(self, mock_registry, mock_logger):
        """Test writing discovered environments to files."""
        mock_envs = {"env_1": MagicMock(), "env_2": MagicMock()}
        mock_registry.keys.return_value = mock_envs.keys()
        
        env_ids = list(mock_envs.keys())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch os.makedirs and file paths
            with patch('os.makedirs'):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__ = lambda s: s
                    mock_open.return_value.__exit__ = lambda s, *args: None
                    
                    write_discovered_envs(env_ids)
                    
                    # Verify files were written
                    assert mock_open.call_count >= 2

    @patch('utils.env_discovery.get_logger')
    @patch('utils.env_discovery.REGISTRY')
    def test_run_discovery_integration(self, mock_registry, mock_logger):
        """Test the full discovery and write flow."""
        mock_envs = {"env_a": MagicMock(), "env_b": MagicMock()}
        mock_registry.keys.return_value = mock_envs.keys()
        
        with patch('os.makedirs'):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__ = lambda s: s
                mock_open.return_value.__exit__ = lambda s, *args: None
                
                result = run_discovery()
                
                assert len(result) == 2
                assert "env_a" in result
                assert "env_b" in result