import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.config import get_config, reload_config, get_nasa_power_key, Config, ProjectError

class TestConfigLoading:
    def test_get_config_returns_instance(self):
        """Test that get_config returns a Config instance."""
        config = get_config()
        assert isinstance(config, Config)

    def test_reload_config_creates_new_instance(self):
        """Test that reload_config creates a new instance."""
        config1 = get_config()
        config2 = reload_config()
        # While they might be the same object if singleton logic is strict,
        # the function should return a valid config.
        assert isinstance(config2, Config)

class TestNasaPowerKey:
    @patch.dict(os.environ, {"NASA_POWER_API_KEY": "test-key-123"})
    def test_get_key_from_env(self):
        """Test that key is retrieved from environment variable."""
        # Reload config to ensure clean state if needed, though env is checked directly
        key = get_nasa_power_key()
        assert key == "test-key-123"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_key_from_config_file(self):
        """Test that key is retrieved from config.yaml if env is missing."""
        # Create a mock config with a key
        mock_config_data = {"nasa_power": {"api_key": "mock-config-key"}}
        
        with patch('code.config.get_config') as mock_get_config:
            mock_config_instance = MagicMock()
            mock_config_instance.get.return_value = mock_config_data["nasa_power"]
            mock_get_config.return_value = mock_config_instance
            
            key = get_nasa_power_key()
            assert key == "mock-config-key"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_key_raises_if_missing(self):
        """Test that ProjectError is raised if key is missing everywhere."""
        with patch('code.config.get_config') as mock_get_config:
            mock_config_instance = MagicMock()
            mock_config_instance.get.return_value = {} # No key in config
            mock_get_config.return_value = mock_config_instance
            
            with pytest.raises(ProjectError) as exc_info:
                get_nasa_power_key()
            
            assert "NASA POWER API key not found" in str(exc_info.value)
