"""
Unit tests for the configuration module.

Tests cover:
- Default configuration initialization
- Custom configuration with required token_limit
- Validation of required fields
- Error handling for invalid values
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import Config, set_config, get_config, validate_config, ConfigurationError


class TestConfigInitialization:
    """Test configuration initialization and defaults."""

    def test_default_config_creation(self):
        """Test that default configuration is created with correct values."""
        config = Config()
        
        assert config.seed == 42
        assert config.batch_size == 4
        assert config.recursion_depth == 2
        assert config.learning_rate == 1e-4
        assert config.token_limit == 100000  # CRITICAL: Must be 100000
        assert config.device == 'cpu'
        assert config.num_workers == 0
        assert config.max_epochs == 10
        assert config.warmup_steps == 100
        assert config.weight_decay == 0.01
        assert config.log_interval == 10
        assert config.save_interval == 100
        assert config.validation_interval == 500

    def test_custom_config_creation(self):
        """Test that custom configuration can be created with overrides."""
        config = Config(
            seed=123,
            batch_size=8,
            recursion_depth=3,
            learning_rate=5e-5,
            token_limit=50000
        )
        
        assert config.seed == 123
        assert config.batch_size == 8
        assert config.recursion_depth == 3
        assert config.learning_rate == 5e-5
        assert config.token_limit == 50000

    def test_token_limit_default_value(self):
        """Test that token_limit defaults to 100000 as required by spec."""
        config = Config()
        assert config.token_limit == 100000

    def test_recursion_depth_default_value(self):
        """Test that recursion_depth defaults to 2."""
        config = Config()
        assert config.recursion_depth == 2


class TestConfigValidation:
    """Test configuration validation logic."""

    def test_valid_config(self):
        """Test that valid configuration passes validation."""
        config = Config()
        config.__post_init__()  # This should not raise
        assert True  # If we get here, validation passed

    def test_invalid_token_limit_negative(self):
        """Test that negative token_limit raises error."""
        with pytest.raises(ConfigurationError):
            config = Config(token_limit=-1)
            config.__post_init__()

    def test_invalid_token_limit_zero(self):
        """Test that zero token_limit raises error."""
        with pytest.raises(ConfigurationError):
            config = Config(token_limit=0)
            config.__post_init__()

    def test_invalid_recursion_depth_zero(self):
        """Test that zero recursion_depth raises error."""
        with pytest.raises(ConfigurationError):
            config = Config(recursion_depth=0)
            config.__post_init__()

    def test_invalid_batch_size(self):
        """Test that non-positive batch_size raises error."""
        with pytest.raises(ConfigurationError):
            config = Config(batch_size=0)
            config.__post_init__()

    def test_invalid_learning_rate(self):
        """Test that non-positive learning_rate raises error."""
        with pytest.raises(ConfigurationError):
            config = Config(learning_rate=0)
            config.__post_init__()

    def test_invalid_seed(self):
        """Test that negative seed raises error."""
        with pytest.raises(ConfigurationError):
            config = Config(seed=-1)
            config.__post_init__()


class TestGlobalConfig:
    """Test global configuration management."""

    def test_set_and_get_config(self):
        """Test setting and getting global configuration."""
        config = Config(token_limit=100000)
        set_config(config)
        
        retrieved = get_config()
        assert retrieved.token_limit == 100000
        assert retrieved is config

    def test_set_config_with_kwargs(self):
        """Test setting global configuration with keyword arguments."""
        set_config(token_limit=100000, seed=999)
        
        config = get_config()
        assert config.token_limit == 100000
        assert config.seed == 999

    def test_get_config_before_set(self):
        """Test that getting config before setting raises error."""
        # Reset global config to None
        import code.config as config_module
        config_module._config = None
        
        with pytest.raises(ConfigurationError):
            get_config()

    def test_validate_config_success(self):
        """Test successful validation of configuration."""
        config = Config(token_limit=100000)
        set_config(config)
        
        result = validate_config()
        assert result is True

    def test_validate_config_failure(self):
        """Test that validation fails for invalid configuration."""
        # Create invalid config
        config = Config(token_limit=-1)
        set_config(config)
        
        with pytest.raises(ConfigurationError):
            validate_config()


class TestConfigSpecRequirements:
    """Test specific requirements from the specification."""

    def test_token_limit_is_integer(self):
        """Test that token_limit is an integer."""
        config = Config()
        assert isinstance(config.token_limit, int)

    def test_token_limit_is_100000(self):
        """Test that token_limit is exactly 100000 as required."""
        config = Config()
        assert config.token_limit == 100000

    def test_recursion_depth_is_2(self):
        """Test that recursion_depth defaults to 2."""
        config = Config()
        assert config.recursion_depth == 2

    def test_seed_is_integer(self):
        """Test that seed is an integer."""
        config = Config()
        assert isinstance(config.seed, int)

    def test_learning_rate_is_float(self):
        """Test that learning_rate is a float."""
        config = Config()
        assert isinstance(config.learning_rate, float)

    def test_batch_size_is_integer(self):
        """Test that batch_size is an integer."""
        config = Config()
        assert isinstance(config.batch_size, int)