"""
Unit tests for the configuration management module.
"""
import pytest
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from utils.config import Config, get_config, set_config, validate_config, ConfigurationError


class TestConfigDataclass:
    """Tests for the Config dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        cfg = Config()
        assert cfg.seed == 42
        assert cfg.batch_size == 4
        assert cfg.recursion_depth == 2
        assert cfg.learning_rate == 5e-5
        assert cfg.token_limit == 100000
        assert cfg.max_steps == 1000
        assert cfg.device == 'cpu'
        assert cfg.log_level == 'INFO'
        assert cfg.n_samples_training == 2
        assert cfg.n_samples_eval == 10

    def test_token_limit_validation_positive(self):
        """Test that positive token_limit is accepted."""
        cfg = Config(token_limit=50000)
        assert cfg.token_limit == 50000

    def test_token_limit_validation_zero(self):
        """Test that zero token_limit raises an error."""
        with pytest.raises(ConfigurationError, match="token_limit must be a positive integer"):
            Config(token_limit=0)

    def test_token_limit_validation_negative(self):
        """Test that negative token_limit raises an error."""
        with pytest.raises(ConfigurationError, match="token_limit must be a positive integer"):
            Config(token_limit=-100)

    def test_recursion_depth_validation(self):
        """Test that recursion_depth < 1 raises an error."""
        with pytest.raises(ConfigurationError, match="recursion_depth must be at least 1"):
            Config(recursion_depth=0)

    def test_batch_size_validation(self):
        """Test that batch_size < 1 raises an error."""
        with pytest.raises(ConfigurationError, match="batch_size must be at least 1"):
            Config(batch_size=0)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        cfg = Config(token_limit=5000)
        d = cfg.to_dict()
        assert d['token_limit'] == 5000
        assert d['seed'] == 42
        assert isinstance(d, dict)

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'token_limit': 20000,
            'recursion_depth': 3,
            'learning_rate': 1e-4
        }
        cfg = Config.from_dict(data)
        assert cfg.token_limit == 20000
        assert cfg.recursion_depth == 3
        assert cfg.learning_rate == 1e-4


class TestGlobalConfig:
    """Tests for global config management functions."""

    def teardown_method(self):
        """Reset global config after each test."""
        from utils.config import _global_config
        # We can't easily reset the private variable directly in a clean way without importing it
        # But we can set it to None by calling set_config with a fresh default
        set_config(Config())

    def test_get_config_creates_default(self):
        """Test that get_config creates a default if none exists."""
        # Force reset by setting a known bad state (simulating None)
        # Since we can't access _global_config easily, we rely on the fact that set_config(Config()) resets it
        set_config(Config())
        
        cfg = get_config()
        assert isinstance(cfg, Config)
        assert cfg.token_limit == 100000

    def test_set_config_updates_global(self):
        """Test that set_config updates the global instance."""
        new_cfg = Config(token_limit=50000, seed=99)
        set_config(new_cfg)
        
        retrieved = get_config()
        assert retrieved.token_limit == 50000
        assert retrieved.seed == 99

    def test_set_config_with_kwargs(self):
        """Test that set_config can update via kwargs."""
        set_config(token_limit=75000, recursion_depth=3)
        cfg = get_config()
        assert cfg.token_limit == 75000
        assert cfg.recursion_depth == 3

    def test_validate_config(self):
        """Test that validate_config returns True for valid config."""
        cfg = Config()
        assert validate_config(cfg) is True

    def test_validate_config_invalid(self):
        """Test that validate_config raises error for invalid config."""
        invalid_cfg = Config(token_limit=-1)
        with pytest.raises(ConfigurationError):
            validate_config(invalid_cfg)