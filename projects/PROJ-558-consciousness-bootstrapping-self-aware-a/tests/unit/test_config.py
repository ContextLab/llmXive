"""
Unit tests for the configuration module.
"""
import pytest
from code.config import Config, validate_config

class TestConfigInitialization:
    """Tests for Config dataclass initialization and defaults."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        cfg = Config()
        assert cfg.seed == 42
        assert cfg.batch_size == 8
        assert cfg.recursion_depth == 2
        assert cfg.learning_rate == 1e-4
        assert cfg.token_limit == 100000
        assert cfg.device == "cpu"
        assert cfg.data_dir == "data"
        assert cfg.output_dir == "artifacts"

    def test_custom_values(self):
        """Test that custom values can be set."""
        cfg = Config(seed=123, batch_size=16, learning_rate=0.01)
        assert cfg.seed == 123
        assert cfg.batch_size == 16
        assert cfg.learning_rate == 0.01
        # Ensure defaults remain for unspecified fields
        assert cfg.recursion_depth == 2
        assert cfg.device == "cpu"

class TestCpuEnforcement:
    """Tests for CPU-only enforcement logic."""

    def test_device_forced_to_cpu(self):
        """Test that device is always forced to 'cpu' regardless of input."""
        # Even if we try to set it to cuda in init, __post_init__ should fix it
        cfg = Config(device="cuda")
        assert cfg.device == "cpu"

    def test_cuda_env_var_removed(self):
        """Test that CUDA_VISIBLE_DEVICES is removed from environment."""
        import os
        # Set a fake CUDA env var
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        
        cfg = Config()
        
        assert "CUDA_VISIBLE_DEVICES" not in os.environ

class TestConstraintValidation:
    """Tests for constraint validation in __post_init__ and validate_config."""

    def test_recursion_depth_min(self):
        """Test that recursion depth < 1 raises ValueError."""
        with pytest.raises(ValueError, match="Recursion depth must be at least 1"):
            Config(recursion_depth=0)

    def test_recursion_depth_max(self):
        """Test that recursion depth > 2 raises ValueError."""
        with pytest.raises(ValueError, match="exceeds the maximum allowed depth of 2"):
            Config(recursion_depth=3)

    def test_token_limit_positive(self):
        """Test that token_limit <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="Token limit must be a positive integer"):
            Config(token_limit=0)

    def test_batch_size_positive(self):
        """Test that batch_size <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="Batch size must be a positive integer"):
            Config(batch_size=-1)

    def test_validate_config_success(self):
        """Test that validate_config returns True for valid config."""
        cfg = Config()
        assert validate_config(cfg) is True

    def test_validate_config_recursion_depth_fail(self):
        """Test that validate_config raises ValueError for invalid recursion depth."""
        cfg = Config(recursion_depth=1) # Valid init
        cfg.recursion_depth = 3 # Manually break invariant
        with pytest.raises(ValueError, match="Invalid recursion_depth"):
            validate_config(cfg)

    def test_validate_config_device_fail(self):
        """Test that validate_config raises ValueError for invalid device."""
        cfg = Config()
        cfg.device = "cuda" # Manually break invariant
        with pytest.raises(ValueError, match="Invalid device"):
            validate_config(cfg)

class TestToDict:
    """Tests for the to_dict method."""

    def test_to_dict_contains_all_fields(self):
        """Test that to_dict returns a dictionary with all expected keys."""
        cfg = Config()
        d = cfg.to_dict()
        
        expected_keys = [
            "seed", "batch_size", "recursion_depth", "learning_rate",
            "token_limit", "device", "data_dir", "output_dir",
            "model_name", "max_steps", "validation_interval", "log_interval"
        ]
        
        for key in expected_keys:
            assert key in d
        
        # Check specific values
        assert d["seed"] == 42
        assert d["device"] == "cpu"
        assert d["recursion_depth"] == 2