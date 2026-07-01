"""
Tests for environment configuration management.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.config import (
    load_env_config,
    set_random_seed,
    validate_config,
    get_config,
    init_config,
    ConfigError,
    DEFAULT_SEED
)

class TestLoadEnvConfig:
    def test_load_config_success(self):
        """Test successful loading of all required environment variables."""
        with patch.dict(os.environ, {
            "DRYAD_API_KEY": "test_dryad_key",
            "ANAGE_API_KEY": "test_anage_key",
            "RANDOM_SEED": "123"
        }):
            config = load_env_config()
            assert config["dryad_api_key"] == "test_dryad_key"
            assert config["anage_api_key"] == "test_anage_key"
            assert config["random_seed"] == 123

    def test_load_config_missing_variables(self):
        """Test that ConfigError is raised when required variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigError) as exc_info:
                load_env_config()
            assert "Missing required environment variables" in str(exc_info.value)
            assert "DRYAD_API_KEY" in str(exc_info.value)
            assert "ANAGE_API_KEY" in str(exc_info.value)
            assert "RANDOM_SEED" in str(exc_info.value)

    def test_load_config_partial_missing(self):
        """Test error message includes only missing variables."""
        with patch.dict(os.environ, {
            "DRYAD_API_KEY": "test_key",
            "RANDOM_SEED": "456"
        }):
            with pytest.raises(ConfigError) as exc_info:
                load_env_config()
            assert "ANAGE_API_KEY" in str(exc_info.value)
            assert "DRYAD_API_KEY" not in str(exc_info.value)

class TestSetRandomSeed:
    def test_set_seed_default(self):
        """Test setting default seed."""
        seed = set_random_seed()
        assert seed == DEFAULT_SEED

    def test_set_seed_custom(self):
        """Test setting custom seed."""
        seed = set_random_seed(999)
        assert seed == 999

    def test_seed_affects_random(self):
        """Test that seed affects Python random module."""
        seed1 = set_random_seed(42)
        val1 = random.random()
        
        seed2 = set_random_seed(42)
        val2 = random.random()
        
        assert val1 == val2

    @patch('code.config.random')
    def test_seed_sets_python_random(self, mock_random):
        """Test that set_random_seed calls random.seed."""
        set_random_seed(123)
        mock_random.seed.assert_called_once_with(123)

    @patch('code.config.np')
    def test_seed_sets_numpy(self, mock_np):
        """Test that set_random_seed sets numpy seed when available."""
        set_random_seed(456)
        mock_np.random.seed.assert_called_once_with(456)

    @patch('code.config.ro')
    def test_seed_sets_r_seed(self, mock_ro):
        """Test that set_random_seed sets R seed when rpy2 is available."""
        set_random_seed(789)
        mock_ro.r['set.seed'].assert_called_once_with(789)

class TestValidateConfig:
    def test_validate_success(self):
        """Test successful validation."""
        with patch.dict(os.environ, {
            "DRYAD_API_KEY": "key1",
            "ANAGE_API_KEY": "key2",
            "RANDOM_SEED": "100"
        }):
            assert validate_config() is True

    def test_validate_missing_vars(self):
        """Test validation fails with missing variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigError):
                validate_config()

class TestGetConfig:
    def test_get_config_complete(self):
        """Test getting full configuration."""
        with patch.dict(os.environ, {
            "DRYAD_API_KEY": "dryad_key",
            "ANAGE_API_KEY": "anage_key",
            "RANDOM_SEED": "555"
        }):
            config = get_config()
            assert "dryad_api_key" in config
            assert "anage_api_key" in config
            assert "random_seed" in config
            assert "seed" in config
            assert config["seed"] == 555

class TestInitConfig:
    @patch('code.config.get_config')
    @patch('builtins.print')
    def test_init_config_calls_get_config(self, mock_print, mock_get_config):
        """Test that init_config calls get_config."""
        mock_get_config.return_value = {"seed": 42}
        result = init_config()
        mock_get_config.assert_called_once()
        assert result["seed"] == 42

    @patch('builtins.print')
    def test_init_config_prints_messages(self, mock_print):
        """Test that init_config prints expected messages."""
        with patch.dict(os.environ, {
            "DRYAD_API_KEY": "key1",
            "ANAGE_API_KEY": "key2",
            "RANDOM_SEED": "123"
        }):
            init_config()
            # Check that expected print statements were called
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Initializing" in call for call in calls)
            assert any("Random seed" in call for call in calls)
            assert any("API keys" in call for call in calls)

# Test imports work correctly
def test_imports():
    """Test that all expected names can be imported."""
    from code.config import (
        load_env_config,
        set_random_seed,
        validate_config,
        get_config,
        init_config,
        ConfigError,
        DEFAULT_SEED
    )
    assert callable(load_env_config)
    assert callable(set_random_seed)
    assert callable(validate_config)
    assert callable(get_config)
    assert callable(init_config)
    assert isinstance(DEFAULT_SEED, int)
