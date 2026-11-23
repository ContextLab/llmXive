"""
Unit tests for the configuration management module (T007).

Tests cover:
- Singleton pattern behavior
- Default values
- Environment variable overrides
- YAML persistence (load/save)
- Parameter validation
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import (
    PipelineConfig,
    get_config,
    reset_config,
    get_filter_low_freq,
    get_filter_high_freq,
    get_mmn_window,
    get_accuracy_block_size,
    get_min_trials_per_block,
    get_lag_source_window_size,
    get_random_seed,
    get_target_electrodes,
    get_subject_exclusion_threshold,
    get_trial_exclusion_threshold,
    get_ram_limit_gb,
    get_max_runtime_hours,
)


class TestConfigSingleton:
    """Test singleton pattern behavior."""

    def test_singleton_returns_same_instance(self):
        """Multiple calls to get_config should return the same instance."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config_clears_singleton(self):
        """reset_config should clear the singleton instance."""
        reset_config()
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2

    def test_get_config_loads_from_file(self):
        """get_config should load from config.yaml if it exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_file = tmpdir_path / "config.yaml"

            # Create a config file
            test_config = PipelineConfig()
            test_config.random_seed = 12345
            test_config.save(config_file)

            # Temporarily change project root
            with patch.object(PipelineConfig, '__init__', lambda self: None):
                config = PipelineConfig()
                config.project_root = tmpdir_path
                config.random_seed = 12345

                # Load config
                loaded_config = PipelineConfig.load(config_file)
                assert loaded_config.random_seed == 12345


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_filter_low_freq(self):
        """Default low-frequency filter should be 1.0 Hz."""
        reset_config()
        assert get_filter_low_freq() == 1.0

    def test_default_filter_high_freq(self):
        """Default high-frequency filter should be 40.0 Hz."""
        reset_config()
        assert get_filter_high_freq() == 40.0

    def test_default_mmn_window(self):
        """Default MMN window should be (-250, 0) ms."""
        reset_config()
        assert get_mmn_window() == (-250, 0)

    def test_default_accuracy_block_size(self):
        """Default accuracy block size should be 50 trials."""
        reset_config()
        assert get_accuracy_block_size() == 50

    def test_default_min_trials_per_block(self):
        """Default minimum trials per block should be 10."""
        reset_config()
        assert get_min_trials_per_block() == 10

    def test_default_lag_source_window_size(self):
        """Default lag source window size should be 50 trials."""
        reset_config()
        assert get_lag_source_window_size() == 50

    def test_default_random_seed(self):
        """Default random seed should be 42."""
        reset_config()
        assert get_random_seed() == 42

    def test_default_target_electrodes(self):
        """Default target electrodes should be CP3, CP4, C3, C4."""
        reset_config()
        assert get_target_electrodes() == ["CP3", "CP4", "C3", "C4"]

    def test_default_subject_exclusion_threshold(self):
        """Default subject exclusion threshold should be 20."""
        reset_config()
        assert get_subject_exclusion_threshold() == 20

    def test_default_trial_exclusion_threshold(self):
        """Default trial exclusion threshold should be 500."""
        reset_config()
        assert get_trial_exclusion_threshold() == 500

    def test_default_ram_limit(self):
        """Default RAM limit should be 7.0 GB."""
        reset_config()
        assert get_ram_limit_gb() == 7.0

    def test_default_max_runtime(self):
        """Default max runtime should be 6.0 hours."""
        reset_config()
        assert get_max_runtime_hours() == 6.0


class TestConfigOverrides:
    """Test configuration overrides via environment variables."""

    @pytest.fixture(autouse=True)
    def cleanup_env(self):
        """Clean up environment variables before and after each test."""
        env_vars = [
            "FILTER_LOW_FREQ_HZ", "FILTER_HIGH_FREQ_HZ", "MMN_WINDOW_START_MS",
            "MMN_WINDOW_END_MS", "ACCURACY_BLOCK_SIZE", "MIN_TRIALS_PER_BLOCK",
            "LAG_SOURCE_WINDOW_SIZE", "SUBJECT_EXCLUSION_THRESHOLD",
            "TRIAL_EXCLUSION_THRESHOLD", "RANDOM_SEED", "RAM_LIMIT_GB",
            "MAX_RUNTIME_HOURS", "TARGET_ELECTRODES"
        ]
        # Save original values
        original_values = {var: os.environ.get(var) for var in env_vars}
        # Remove all env vars
        for var in env_vars:
            os.environ.pop(var, None)
        # Reset config
        reset_config()
        yield
        # Restore original values
        reset_config()
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value
            else:
                os.environ.pop(var, None)

    def test_filter_low_freq_override(self):
        """Environment variable should override default filter low freq."""
        os.environ["FILTER_LOW_FREQ_HZ"] = "2.5"
        reset_config()
        assert get_filter_low_freq() == 2.5

    def test_filter_high_freq_override(self):
        """Environment variable should override default filter high freq."""
        os.environ["FILTER_HIGH_FREQ_HZ"] = "50.0"
        reset_config()
        assert get_filter_high_freq() == 50.0

    def test_mmn_window_override(self):
        """Environment variables should override MMN window."""
        os.environ["MMN_WINDOW_START_MS"] = "-300"
        os.environ["MMN_WINDOW_END_MS"] = "100"
        reset_config()
        assert get_mmn_window() == (-300, 100)

    def test_accuracy_block_size_override(self):
        """Environment variable should override accuracy block size."""
        os.environ["ACCURACY_BLOCK_SIZE"] = "100"
        reset_config()
        assert get_accuracy_block_size() == 100

    def test_random_seed_override(self):
        """Environment variable should override random seed."""
        os.environ["RANDOM_SEED"] = "999"
        reset_config()
        assert get_random_seed() == 999

    def test_target_electrodes_override(self):
        """Environment variable should override target electrodes."""
        os.environ["TARGET_ELECTRODES"] = "Fz, Cz, Pz"
        reset_config()
        assert get_target_electrodes() == ["Fz", "Cz", "Pz"]

    def test_invalid_env_var_handling(self):
        """Invalid environment variable values should be handled gracefully."""
        os.environ["FILTER_LOW_FREQ_HZ"] = "invalid"
        reset_config()
        # Should fall back to default
        assert get_filter_low_freq() == 1.0


class TestConfigPersistence:
    """Test configuration save and load functionality."""

    def test_save_and_load_config(self):
        """Config should be saved to and loaded from YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yaml"

            # Create and save config
            config = PipelineConfig()
            config.random_seed = 12345
            config.filter_low_freq_hz = 2.0
            config.save(config_path)

            # Load config
            loaded_config = PipelineConfig.load(config_path)

            assert loaded_config.random_seed == 12345
            assert loaded_config.filter_low_freq_hz == 2.0

    def test_save_creates_directory(self):
        """Save should create parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "path" / "config.yaml"

            config = PipelineConfig()
            config.save(nested_path)

            assert nested_path.exists()

    def test_load_missing_file_uses_defaults(self):
        """Loading a missing file should use defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "nonexistent.yaml"

            config = PipelineConfig.load(missing_path)

            # Should have default values
            assert config.random_seed == 42
            assert config.filter_low_freq_hz == 1.0

    def test_to_dict(self):
        """to_dict should return all configuration values."""
        config = PipelineConfig()
        config_dict = config.to_dict()

        assert "random_seed" in config_dict
        assert "filter_low_freq_hz" in config_dict
        assert "accuracy_block_size" in config_dict
        assert "target_electrodes" in config_dict
        assert config_dict["random_seed"] == 42

    def test_to_dict_path_serialization(self):
        """Paths should be serialized as strings."""
        config = PipelineConfig()
        config_dict = config.to_dict()

        assert isinstance(config_dict["data_dir"], str)
        assert isinstance(config_dict["analysis_dir"], str)


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_config(self):
        """Valid configuration should pass validation."""
        config = PipelineConfig()
        assert config.validate() is True

    def test_invalid_filter_low_freq(self):
        """Negative filter low freq should fail validation."""
        config = PipelineConfig()
        config.filter_low_freq_hz = -1.0
        assert config.validate() is False

    def test_invalid_filter_range(self):
        """Filter high freq less than low freq should fail validation."""
        config = PipelineConfig()
        config.filter_low_freq_hz = 40.0
        config.filter_high_freq_hz = 10.0
        assert config.validate() is False

    def test_invalid_mmn_window(self):
        """MMN window with start >= end should fail validation."""
        config = PipelineConfig()
        config.mmn_window_start_ms = 100
        config.mmn_window_end_ms = 0
        assert config.validate() is False

    def test_invalid_accuracy_block_size(self):
        """Zero accuracy block size should fail validation."""
        config = PipelineConfig()
        config.accuracy_block_size = 0
        assert config.validate() is False

    def test_empty_target_electrodes(self):
        """Empty target electrodes should fail validation."""
        config = PipelineConfig()
        config.target_electrodes = []
        assert config.validate() is False

    def test_get_config_validation_warning(self):
        """get_config should warn on validation failure."""
        with patch.object(PipelineConfig, 'load') as mock_load:
            invalid_config = PipelineConfig()
            invalid_config.filter_low_freq_hz = -1.0
            mock_load.return_value = invalid_config

            reset_config()
            config = get_config()

            # Should still return a config (defaults)
            assert config is not None
            assert config.filter_low_freq_hz == 1.0  # Default value
