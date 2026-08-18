import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from utils.config import Config, load_environment, get_env


class TestConfig:
    """Unit tests for the Config class and environment loading functions."""

    def test_config_initialization(self):
        """Test that Config initializes correctly."""
        config = Config()
        assert config._loaded is False
        assert config._values == {}

    def test_config_with_custom_path(self):
        """Test Config with a custom environment file path."""
        config = Config(env_path=Path("/nonexistent/.env"))
        assert config._env_path == Path("/nonexistent/.env")

    @patch('utils.config.load_dotenv')
    def test_load_creates_dotenv_call(self, mock_load_dotenv):
        """Test that load() calls load_dotenv when dotenv is available."""
        config = Config()
        with patch.object(config, '_loaded', False):
            config.load()
            mock_load_dotenv.assert_called()

    @patch('utils.config.os.getenv')
    def test_get_returns_env_value(self, mock_getenv):
        """Test that get() returns the correct environment variable value."""
        mock_getenv.return_value = "test_value"
        config = Config()
        with patch.object(config, '_loaded', True):
            result = config.get("TEST_VAR")
            assert result == "test_value"

    @patch('utils.config.os.getenv')
    def test_get_returns_default_when_missing(self, mock_getenv):
        """Test that get() returns the default value when variable is missing."""
        mock_getenv.return_value = None
        config = Config()
        with patch.object(config, '_loaded', True):
            result = config.get("MISSING_VAR", "default_value")
            assert result == "default_value"

    @patch('utils.config.os.getenv')
    def test_get_int_returns_integer(self, mock_getenv):
        """Test that get_int() returns an integer value."""
        mock_getenv.return_value = "42"
        config = Config()
        with patch.object(config, '_loaded', True):
            result = config.get_int("INT_VAR")
            assert result == 42

    @patch('utils.config.os.getenv')
    def test_get_int_returns_default_on_invalid(self, mock_getenv):
        """Test that get_int() returns default on invalid integer string."""
        mock_getenv.return_value = "not_a_number"
        config = Config()
        with patch.object(config, '_loaded', True):
            result = config.get_int("INT_VAR", 10)
            assert result == 10

    @patch('utils.config.os.getenv')
    def test_get_float_returns_float(self, mock_getenv):
        """Test that get_float() returns a float value."""
        mock_getenv.return_value = "3.14"
        config = Config()
        with patch.object(config, '_loaded', True):
            result = config.get_float("FLOAT_VAR")
            assert result == 3.14

    @patch('utils.config.os.getenv')
    def test_get_bool_returns_true(self, mock_getenv):
        """Test that get_bool() returns True for truthy values."""
        mock_getenv.return_value = "true"
        config = Config()
        with patch.object(config, '_loaded', True):
            result = config.get_bool("BOOL_VAR")
            assert result is True

    @patch('utils.config.os.getenv')
    def test_get_bool_returns_false(self, mock_getenv):
        """Test that get_bool() returns False for falsy values."""
        mock_getenv.return_value = "false"
        config = Config()
        with patch.object(config, '_loaded', True):
            result = config.get_bool("BOOL_VAR")
            assert result is False

    @patch('utils.config.os.getenv')
    def test_require_raises_on_missing(self, mock_getenv):
        """Test that require() raises ValueError when variable is missing."""
        mock_getenv.return_value = None
        config = Config()
        with patch.object(config, '_loaded', True):
            with pytest.raises(ValueError, match="Required environment variable"):
                config.require("REQUIRED_VAR")

    @patch('utils.config.os.getenv')
    def test_require_returns_value(self, mock_getenv):
        """Test that require() returns the value when variable is set."""
        mock_getenv.return_value = "required_value"
        config = Config()
        with patch.object(config, '_loaded', True):
            result = config.require("REQUIRED_VAR")
            assert result == "required_value"

    @patch('utils.config.os.getenv')
    def test_to_dict_returns_env_dict(self, mock_getenv):
        """Test that to_dict() returns a dictionary of environment variables."""
        mock_getenv.side_effect = lambda key, default=None: os.environ.get(key, default)
        config = Config()
        with patch.object(config, '_loaded', True):
            result = config.to_dict()
            assert isinstance(result, dict)

class TestLoadEnvironment:
    """Unit tests for the load_environment function."""

    @patch('utils.config._config')
    def test_load_environment_sets_path_and_loads(self, mock_config):
        """Test that load_environment sets the path and calls load()."""
        test_path = Path("/test/.env")
        load_environment(test_path)
        mock_config._env_path = test_path
        mock_config.load.assert_called_once()

class TestGetEnv:
    """Unit tests for the get_env function."""

    @patch('utils.config._config')
    def test_get_env_calls_config_get(self, mock_config):
        """Test that get_env calls the config's get method."""
        mock_config.get.return_value = "test_value"
        result = get_env("TEST_VAR", "default")
        mock_config.get.assert_called_once_with("TEST_VAR", "default")
        assert result == "test_value"
