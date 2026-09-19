"""
Tests for configuration management module.
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import (
    load_config,
    save_config,
    get_random_seed,
    set_random_seed,
    initialize_random_state,
    get_data_dir,
    get_raw_data_dir,
    get_processed_data_dir,
    get_figures_dir,
    get_output_dir,
    get_log_level,
    get_simulation_config,
    get_random_generator,
    get_np_random_generator,
    DEFAULT_CONFIG
)


class TestConfigLoading:
    """Test configuration loading and saving."""

    def test_load_default_config(self, tmp_path):
        """Test loading default config when file doesn't exist."""
        config_path = tmp_path / "nonexistent" / "config.json"

        config = load_config(config_path)

        assert config["random_seed"] == 42
        assert config["log_level"] == "INFO"
        assert "simulation" in config
        assert "datasets" in config

    def test_save_and_load_config(self, tmp_path):
        """Test saving and loading a custom config."""
        config_path = tmp_path / "config.json"
        custom_config = {
            "random_seed": 123,
            "log_level": "DEBUG",
            "simulation": {
                "n_replications": 500
            }
        }

        save_config(custom_config, config_path)
        loaded_config = load_config(config_path)

        assert loaded_config["random_seed"] == 123
        assert loaded_config["log_level"] == "DEBUG"
        assert loaded_config["simulation"]["n_replications"] == 500
        # Default values should be preserved
        assert loaded_config["simulation"]["confidence_levels"] == DEFAULT_CONFIG["simulation"]["confidence_levels"]

    def test_merge_defaults_with_custom(self, tmp_path):
        """Test that missing keys are filled with defaults."""
        config_path = tmp_path / "config.json"
        partial_config = {
            "random_seed": 999
        }

        save_config(partial_config, config_path)
        loaded_config = load_config(config_path)

        assert loaded_config["random_seed"] == 999
        assert loaded_config["log_level"] == "INFO"  # Default
        assert "simulation" in loaded_config  # Default section


class TestRandomSeedManagement:
    """Test random seed management functionality."""

    def test_get_random_seed_default(self):
        """Test getting default random seed."""
        # Reset to default by initializing with default config
        initialize_random_state(42)
        assert get_random_seed() == 42

    def test_set_random_seed(self):
        """Test setting random seed."""
        set_random_seed(12345)
        assert get_random_seed() == 12345

    def test_initialize_random_state(self):
        """Test random state initialization."""
        initialize_random_state(42)
        rng = get_random_generator()
        np_rng = get_np_random_generator()

        # Should produce deterministic results
        assert rng.random() == 0.6394267984578837
        assert np_rng.random() == 0.6394267984578837

    def test_reproducible_randomness(self):
        """Test that same seed produces same results."""
        initialize_random_state(42)
        rng1 = get_random_generator()
        val1 = rng1.random()

        initialize_random_state(42)
        rng2 = get_random_generator()
        val2 = rng2.random()

        assert val1 == val2


class TestDirectoryPaths:
    """Test directory path getters."""

    def test_get_data_dir(self):
        """Test getting data directory."""
        path = get_data_dir()
        assert path.exists() or str(path).endswith("data")

    def test_get_raw_data_dir(self):
        """Test getting raw data directory."""
        path = get_raw_data_dir()
        assert "raw" in str(path)

    def test_get_processed_data_dir(self):
        """Test getting processed data directory."""
        path = get_processed_data_dir()
        assert "processed" in str(path)

    def test_get_figures_dir(self):
        """Test getting figures directory."""
        path = get_figures_dir()
        assert "figures" in str(path)

    def test_get_output_dir(self):
        """Test getting output directory."""
        path = get_output_dir()
        assert "outputs" in str(path)


class TestConfigurationAccessors:
    """Test configuration accessor functions."""

    def test_get_log_level(self):
        """Test getting log level."""
        level = get_log_level()
        assert level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_get_simulation_config(self):
        """Test getting simulation config."""
        sim_config = get_simulation_config()
        assert "n_replications" in sim_config
        assert "confidence_levels" in sim_config
        assert "sample_sizes" in sim_config
        assert "bootstrap_resamples" in sim_config

    def test_get_random_generator(self):
        """Test getting random generator."""
        rng = get_random_generator()
        assert rng is not None
        assert rng.random() is not None

    def test_get_np_random_generator(self):
        """Test getting numpy random generator."""
        rng = get_np_random_generator()
        assert rng is not None
        assert rng.random() is not None
