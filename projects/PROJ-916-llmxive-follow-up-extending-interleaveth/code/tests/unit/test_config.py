"""
Unit tests for src/config.py
"""
import os
import pytest
from src.config import Config, get_config, reset_config


class TestConfigDataclass:
    """Tests for the Config dataclass defaults and validation."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        cfg = Config()
        assert cfg.random_seed == 42
        assert cfg.torch_seed == 42
        assert cfg.numpy_seed == 42
        assert cfg.critic_thresholds == [0.7, 0.8, 0.9]
        assert cfg.default_critic_threshold == 0.8
        assert cfg.train_batch_size == 16
        assert cfg.eval_batch_size == 32
        assert cfg.simulator_batch_size == 64
        assert cfg.generator_timeout_seconds == 30
        assert cfg.max_memory_gb == 7.0
        assert cfg.max_runtime_hours == 6
        assert cfg.use_cpu is True

    def test_validate_thresholds_valid(self):
        """Test validation passes for valid thresholds."""
        cfg = Config(critic_thresholds=[0.5, 0.6, 0.7], default_critic_threshold=0.6)
        cfg.validate()  # Should not raise

    def test_validate_thresholds_invalid_range(self):
        """Test validation fails for thresholds outside 0-1."""
        cfg = Config(critic_thresholds=[0.5, 1.5], default_critic_threshold=0.5)
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            cfg.validate()

    def test_validate_thresholds_default_not_in_list(self):
        """Test validation fails if default is not in the list."""
        cfg = Config(critic_thresholds=[0.7, 0.8], default_critic_threshold=0.9)
        with pytest.raises(ValueError, match="must be one of the configured"):
            cfg.validate()

    def test_validate_max_memory_positive(self):
        """Test validation fails for non-positive max memory."""
        cfg = Config(max_memory_gb=0)
        with pytest.raises(ValueError, match="must be positive"):
            cfg.validate()

    def test_validate_timeout_positive(self):
        """Test validation fails for non-positive timeout."""
        cfg = Config(generator_timeout_seconds=-1)
        with pytest.raises(ValueError, match="must be positive"):
            cfg.validate()


class TestConfigFromEnv:
    """Tests for loading configuration from environment variables."""

    def setup_method(self):
        """Clean environment before each test."""
        reset_config()
        # Remove specific env vars to ensure clean state
        vars_to_remove = [
            "LLMXIVE_RANDOM_SEED", "LLMXIVE_TORCH_SEED", "LLMXIVE_NUMPY_SEED",
            "LLMXIVE_CRITIC_THRESHOLDS", "LLMXIVE_DEFAULT_CRITIC_THRESHOLD",
            "LLMXIVE_TRAIN_BATCH_SIZE", "LLMXIVE_EVAL_BATCH_SIZE",
            "LLMXIVE_SIMULATOR_BATCH_SIZE", "LLMXIVE_GENERATOR_TIMEOUT",
            "LLMXIVE_MAX_MEMORY_GB", "LLMXIVE_MAX_RUNTIME_HOURS",
            "LLMXIVE_DATA_RAW_DIR", "LLMXIVE_DATA_INTERMEDIATE_DIR",
            "LLMXIVE_DATA_SIMULATOR_VALIDATION_DIR", "LLMXIVE_SPECS_DIR",
            "LLMXIVE_WISE_AVAILABLE", "LLMXIVE_RISE_AVAILABLE",
            "LLMXIVE_VG_AVAILABLE", "LLMXIVE_GQA_AVAILABLE",
            "LLMXIVE_LOG_LEVEL", "LLMXIVE_LOG_FILE",
            "LLMXIVE_GENERATOR_MODEL", "LLMXIVE_CRITIC_MODEL",
            "LLMXIVE_USE_CPU", "LLMXIVE_USE_BFLOAT16"
        ]
        for var in vars_to_remove:
            os.environ.pop(var, None)

    def teardown_method(self):
        """Clean environment after each test."""
        self.setup_method()

    def test_from_env_defaults(self):
        """Test that from_env returns defaults when no env vars are set."""
        cfg = Config.from_env()
        assert cfg.random_seed == 42
        assert cfg.critic_thresholds == [0.7, 0.8, 0.9]

    def test_from_env_custom_values(self):
        """Test that from_env reads custom values from environment."""
        os.environ["LLMXIVE_RANDOM_SEED"] = "123"
        os.environ["LLMXIVE_CRITIC_THRESHOLDS"] = "0.1,0.2,0.3"
        os.environ["LLMXIVE_DEFAULT_CRITIC_THRESHOLD"] = "0.2"
        os.environ["LLMXIVE_MAX_MEMORY_GB"] = "10.5"
        os.environ["LLMXIVE_WISE_AVAILABLE"] = "false"
        os.environ["LLMXIVE_USE_CPU"] = "false"

        cfg = Config.from_env()
        assert cfg.random_seed == 123
        assert cfg.critic_thresholds == [0.1, 0.2, 0.3]
        assert cfg.default_critic_threshold == 0.2
        assert cfg.max_memory_gb == 10.5
        assert cfg.wise_available is False
        assert cfg.use_cpu is False

    def test_from_env_boolean_parsing(self):
        """Test boolean parsing for various string inputs."""
        os.environ["LLMXIVE_WISE_AVAILABLE"] = "True"
        os.environ["LLMXIVE_RISE_AVAILABLE"] = "TRUE"
        os.environ["LLMXIVE_VG_AVAILABLE"] = "false"
        os.environ["LLMXIVE_GQA_AVAILABLE"] = "False"
        
        cfg = Config.from_env()
        assert cfg.wise_available is True
        assert cfg.rise_available is True
        assert cfg.vg_available is False
        assert cfg.gqa_available is False

class TestGetConfig:
    """Tests for the global config getter."""

    def setup_method(self):
        reset_config()

    def teardown_method(self):
        reset_config()

    def test_get_config_initializes(self):
        """Test that get_config initializes the global config."""
        cfg = get_config()
        assert cfg is not None
        assert isinstance(cfg, Config)

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_get_config_respects_env(self):
        """Test that get_config respects environment variables."""
        os.environ["LLMXIVE_RANDOM_SEED"] = "999"
        cfg = get_config()
        assert cfg.random_seed == 999

    def test_reset_config_clears_singleton(self):
        """Test that reset_config clears the global instance."""
        get_config()
        reset_config()
        cfg = get_config()
        assert cfg.random_seed == 42  # Should be default again