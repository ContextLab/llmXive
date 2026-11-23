"""
Unit tests for src/config.py configuration management.
"""
import os
import pytest
from src.config import Config, get_config, reset_config


class TestConfigDataclass:
    """Tests for the Config dataclass structure and defaults."""

    def test_default_values(self):
        """Verify default values are set correctly."""
        config = Config()
        assert config.random_seed == 42
        assert config.critic_thresholds == [0.7, 0.8, 0.9]
        assert config.default_critic_threshold == 0.8
        assert config.batch_size == 8
        assert config.eval_batch_size == 4
        assert config.max_steps_per_sample == 10
        assert config.timeout_per_sample_seconds == 30
        assert config.memory_limit_gb == 7.0
        assert config.simulation_mode == "Noisy"
        assert config.device == "cpu"

    def test_custom_values(self):
        """Verify custom values can be set."""
        config = Config(
            random_seed=123,
            critic_thresholds=[0.5, 0.6],
            batch_size=16,
            simulation_mode="Perfect",
        )
        assert config.random_seed == 123
        assert config.critic_thresholds == [0.5, 0.6]
        assert config.batch_size == 16
        assert config.simulation_mode == "Perfect"


class TestConfigFromEnv:
    """Tests for environment variable loading."""

    def test_from_env_with_defaults(self):
        """Test loading config when no env vars are set."""
        # Ensure no env vars interfere
        for key in [
            "LLMXIVE_RANDOM_SEED", "LLMXIVE_BATCH_SIZE", "LLMXIVE_SIMULATION_MODE"
        ]:
            os.environ.pop(key, None)

        config = Config.from_env()
        assert config.random_seed == 42
        assert config.batch_size == 8
        assert config.simulation_mode == "Noisy"

    def test_from_env_with_custom_values(self):
        """Test loading config from custom environment variables."""
        try:
            os.environ["LLMXIVE_RANDOM_SEED"] = "999"
            os.environ["LLMXIVE_BATCH_SIZE"] = "32"
            os.environ["LLMXIVE_SIMULATION_MODE"] = "Perfect"
            os.environ["LLMXIVE_CRITIC_THRESHOLDS"] = "0.5,0.9"

            config = Config.from_env()

            assert config.random_seed == 999
            assert config.batch_size == 32
            assert config.simulation_mode == "Perfect"
            assert config.critic_thresholds == [0.5, 0.9]
        finally:
            # Cleanup
            for key in [
                "LLMXIVE_RANDOM_SEED", "LLMXIVE_BATCH_SIZE",
                "LLMXIVE_SIMULATION_MODE", "LLMXIVE_CRITIC_THRESHOLDS"
            ]:
                os.environ.pop(key, None)


class TestGetConfig:
    """Tests for the singleton get_config/reset_config functions."""

    def test_get_config_initialization(self):
        """Test that get_config initializes the singleton."""
        reset_config()
        config1 = get_config()
        assert config1 is not None
        assert isinstance(config1, Config)

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config(self):
        """Test that reset_config clears the singleton."""
        reset_config()
        _ = get_config()
        reset_config()
        config_new = get_config()
        # Should be a new instance after reset
        assert config_new is not None

    def test_config_isolation(self):
        """Test that modifying one config doesn't affect others after reset."""
        reset_config()
        config1 = get_config()
        original_seed = config1.random_seed
        config1.random_seed = 12345

        reset_config()
        config2 = get_config()
        assert config2.random_seed == original_seed  # Should be default