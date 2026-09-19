"""
Unit tests for the configuration management module.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

# Import the module to test
from utils.config import (
    load_environment,
    get_env,
    get_config,
    validate_config,
    Config,
    DEFAULT_RUN_MODE,
    DEFAULT_RANDOM_SEED,
    VALID_RUN_MODES,
)


class TestLoadEnvironment:
    def test_load_environment_existing_file(self, tmp_path):
        """Test loading from an existing .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\n")

        with patch("utils.config.load_dotenv") as mock_load_dotenv:
            result = load_environment(env_file)
            mock_load_dotenv.assert_called_once()
            assert result is True

    def test_load_environment_missing_file(self):
        """Test loading from a non-existent .env file."""
        with patch("utils.config.logger") as mock_logger:
            result = load_environment(Path("/nonexistent/.env"))
            assert result is False
            mock_logger.warning.assert_called()

    def test_load_environment_default_path(self, tmp_path):
        """Test loading from default path (project root .env)."""
        # Create a .env in a temp directory and mock the project root
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\n")

        # Mock Path(__file__).resolve().parent.parent.parent to return tmp_path
        with patch("utils.config.Path") as mock_path_class:
            mock_path_instance = MagicMock()
            mock_path_instance.return_value = tmp_path
            mock_path_class.return_value = mock_path_instance

            with patch("utils.config.load_dotenv") as mock_load_dotenv:
                load_environment()
                mock_load_dotenv.assert_called_once()


class TestGetEnv:
    def test_get_env_existing(self):
        """Test getting an existing environment variable."""
        os.environ["TEST_VAR"] = "test_value"
        assert get_env("TEST_VAR") == "test_value"

    def test_get_env_missing(self):
        """Test getting a missing environment variable."""
        if "NONEXISTENT_VAR" in os.environ:
            del os.environ["NONEXISTENT_VAR"]
        assert get_env("NONEXISTENT_VAR") is None

    def test_get_env_with_default(self):
        """Test getting a missing variable with a default."""
        assert get_env("NONEXISTENT_VAR", "default_value") == "default_value"


class TestGetConfig:
    @patch("utils.config.load_environment")
    def test_get_config_defaults(self, mock_load_env):
        """Test that get_config returns default values when env vars are missing."""
        mock_load_env.return_value = True
        # Clear relevant env vars
        for key in ["RUN_MODE", "RANDOM_SEED", "LOG_LEVEL", "PERMUTATION_ITERATIONS"]:
            if key in os.environ:
                del os.environ[key]

        config = get_config()

        assert config["RUN_MODE"] == DEFAULT_RUN_MODE
        assert config["RANDOM_SEED"] == DEFAULT_RANDOM_SEED
        assert config["LOG_LEVEL"] == "INFO"
        assert config["PERMUTATION_ITERATIONS"] == DEFAULT_PERMUTATION_ITERATIONS

    @patch("utils.config.load_environment")
    def test_get_config_custom_values(self, mock_load_env):
        """Test get_config with custom environment variables."""
        mock_load_env.return_value = True
        os.environ["RUN_MODE"] = "test"
        os.environ["RANDOM_SEED"] = "123"
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["PERMUTATION_ITERATIONS"] = "500"

        config = get_config()

        assert config["RUN_MODE"] == "test"
        assert config["RANDOM_SEED"] == 123
        assert config["LOG_LEVEL"] == "DEBUG"
        assert config["PERMUTATION_ITERATIONS"] == 500

        # Cleanup
        for key in ["RUN_MODE", "RANDOM_SEED", "LOG_LEVEL", "PERMUTATION_ITERATIONS"]:
            del os.environ[key]

    @patch("utils.config.load_environment")
    def test_get_config_invalid_run_mode(self, mock_load_env):
        """Test get_config raises error for invalid RUN_MODE."""
        mock_load_env.return_value = True
        os.environ["RUN_MODE"] = "invalid_mode"

        with pytest.raises(ValueError, match="Invalid RUN_MODE"):
            get_config()

        del os.environ["RUN_MODE"]

    @patch("utils.config.load_environment")
    def test_get_config_invalid_random_seed(self, mock_load_env):
        """Test get_config raises error for non-integer RANDOM_SEED."""
        mock_load_env.return_value = True
        os.environ["RANDOM_SEED"] = "not_an_int"

        with pytest.raises(ValueError, match="RANDOM_SEED must be an integer"):
            get_config()

        del os.environ["RANDOM_SEED"]

    @patch("utils.config.load_environment")
    def test_get_config_invalid_permutations(self, mock_load_env):
        """Test get_config raises error for non-positive PERMUTATION_ITERATIONS."""
        mock_load_env.return_value = True
        os.environ["PERMUTATION_ITERATIONS"] = "-10"

        with pytest.raises(ValueError, match="PERMUTATION_ITERATIONS must be a positive integer"):
            get_config()

        del os.environ["PERMUTATION_ITERATIONS"]


class TestConfigClass:
    @patch("utils.config.get_config")
    def test_config_singleton(self, mock_get_config):
        """Test that Config is a singleton."""
        mock_get_config.return_value = {"RUN_MODE": "test", "RANDOM_SEED": 42}

        config1 = Config()
        config2 = Config()

        assert config1 is config2

    @patch("utils.config.get_config")
    def test_config_get(self, mock_get_config):
        """Test Config.get method."""
        mock_get_config.return_value = {"RUN_MODE": "production", "RANDOM_SEED": 99}

        config = Config()
        assert config.get("RUN_MODE") == "production"
        assert config.get("RANDOM_SEED") == 99
        assert config.get("MISSING", "default") == "default"

    @patch("utils.config.get_config")
    def test_config_run_mode_helpers(self, mock_get_config):
        """Test Config run mode helper methods."""
        mock_get_config.return_value = {"RUN_MODE": "test", "RANDOM_SEED": 42}

        config = Config()
        assert config.is_test() is True
        assert config.is_production() is False

        mock_get_config.return_value = {"RUN_MODE": "production", "RANDOM_SEED": 42}
        # Note: Singleton caches the first config, so we need a new instance for testing
        Config._instance = None
        config2 = Config()
        assert config2.is_production() is True
        assert config2.is_test() is False