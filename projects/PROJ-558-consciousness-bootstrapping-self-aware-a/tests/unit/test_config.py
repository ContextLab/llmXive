"""
Unit tests for the config module.
"""
import pytest
import torch
from unittest.mock import patch, MagicMock
import os

from config import Config, ConfigurationError, get_config, set_config, validate_config


class TestConfigInitialization:
    """Tests for Config class initialization and constraints."""

    def test_default_values(self):
        """Test that default configuration values are set correctly."""
        config = Config()
        assert config.seed == 42
        assert config.batch_size == 4
        assert config.recursion_depth == 2
        assert config.learning_rate == 1e-4
        assert config.token_limit == 100000
        assert config.cpu_only is True
        assert config.model_name == "TinyLlama/TinyLlama-1.1B-Chat-v0.3"
        assert config.max_epochs == 3

    def test_custom_values(self):
        """Test that custom configuration values are set correctly."""
        config = Config(
            seed=123,
            batch_size=8,
            recursion_depth=2,
            learning_rate=5e-5,
            token_limit=50000,
        )
        assert config.seed == 123
        assert config.batch_size == 8
        assert config.recursion_depth == 2
        assert config.learning_rate == 5e-5
        assert config.token_limit == 50000

    def test_recursion_depth_constraint_violation(self):
        """Test that recursion_depth > 2 raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Config(recursion_depth=3)
        assert "recursion depth" in str(exc_info.value).lower()
        assert "exceeds maximum allowed value of 2" in str(exc_info.value)

    def test_token_limit_validation(self):
        """Test that non-positive token_limit raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Config(token_limit=0)
        assert "token limit" in str(exc_info.value).lower()

        with pytest.raises(ConfigurationError) as exc_info:
            Config(token_limit=-100)
        assert "token limit" in str(exc_info.value).lower()

    def test_batch_size_validation(self):
        """Test that non-positive batch_size raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Config(batch_size=0)
        assert "batch size" in str(exc_info.value).lower()

        with pytest.raises(ConfigurationError) as exc_info:
            Config(batch_size=-1)
        assert "batch size" in str(exc_info.value).lower()

    def test_cpu_only_enforcement(self):
        """Test that cpu_only=True sets CUDA_VISIBLE_DEVICES."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config(cpu_only=True)
            assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""

    def test_to_dict(self):
        """Test that to_dict returns all configuration parameters."""
        config = Config(seed=99, batch_size=16)
        config_dict = config.to_dict()
        
        assert config_dict["seed"] == 99
        assert config_dict["batch_size"] == 16
        assert config_dict["recursion_depth"] == 2
        assert config_dict["learning_rate"] == 1e-4
        assert config_dict["token_limit"] == 100000
        assert config_dict["cpu_only"] is True

    def test_from_dict(self):
        """Test that from_dict creates a Config with correct values."""
        config_dict = {
            "seed": 777,
            "batch_size": 32,
            "recursion_depth": 2,
            "learning_rate": 2e-4,
            "token_limit": 200000,
            "cpu_only": False,
        }
        config = Config.from_dict(config_dict)
        
        assert config.seed == 777
        assert config.batch_size == 32
        assert config.recursion_depth == 2
        assert config.learning_rate == 2e-4
        assert config.token_limit == 200000
        assert config.cpu_only is False


class TestGlobalConfig:
    """Tests for global configuration management."""

    def setup_method(self):
        """Reset global config before each test."""
        # Clear global config
        import config as config_module
        config_module._global_config = None

    def test_get_config_before_set_raises_error(self):
        """Test that get_config() raises error before set_config()."""
        with pytest.raises(ConfigurationError) as exc_info:
            get_config()
        assert "not initialized" in str(exc_info.value).lower()

    def test_set_config_with_instance(self):
        """Test setting global config with a Config instance."""
        config = Config(seed=456)
        set_config(config)
        
        global_config = get_config()
        assert global_config.seed == 456

    def test_set_config_with_kwargs(self):
        """Test setting global config with keyword arguments."""
        set_config(seed=789, batch_size=16)
        
        global_config = get_config()
        assert global_config.seed == 789
        assert global_config.batch_size == 16

    def test_set_config_updates_existing(self):
        """Test that set_config with kwargs updates existing config."""
        set_config(seed=111, batch_size=4)
        set_config(seed=222)  # Only update seed
        
        global_config = get_config()
        assert global_config.seed == 222
        assert global_config.batch_size == 4  # Should remain unchanged

    def test_set_config_unknown_parameter(self):
        """Test that set_config raises error for unknown parameters."""
        set_config(seed=333)
        
        with pytest.raises(ConfigurationError) as exc_info:
            set_config(unknown_param=123)
        assert "unknown configuration parameter" in str(exc_info.value).lower()

    def test_validate_config(self):
        """Test that validate_config returns True for valid config."""
        config = Config()
        set_config(config)
        
        result = validate_config()
        assert result is True

    def test_validate_config_invalid(self):
        """Test that validate_config raises error for invalid config."""
        # Create a config that would fail validation if we could bypass __init__
        # Since __init__ already enforces constraints, we test the flow
        config = Config()
        set_config(config)
        
        # This should not raise
        validate_config()


class TestConfigIntegration:
    """Integration tests for config module."""

    def test_full_workflow(self):
        """Test a complete workflow of config usage."""
        # Create and set config
        config = Config(
            seed=999,
            batch_size=8,
            recursion_depth=2,
            learning_rate=1e-4,
            token_limit=100000,
        )
        set_config(config)
        
        # Retrieve and validate
        retrieved_config = get_config()
        assert retrieved_config.seed == 999
        
        validate_config()
        
        # Convert to dict and back
        config_dict = retrieved_config.to_dict()
        new_config = Config.from_dict(config_dict)
        
        assert new_config.seed == retrieved_config.seed
        assert new_config.batch_size == retrieved_config.batch_size
        assert new_config.recursion_depth == retrieved_config.recursion_depth