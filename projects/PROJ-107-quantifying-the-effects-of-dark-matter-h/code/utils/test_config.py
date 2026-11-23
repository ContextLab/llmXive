"""
Unit tests for the configuration management module.
"""
import pytest
from pathlib import Path
import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config import (
    get_project_root,
    get_data_raw_path,
    get_data_processed_path,
    get_output_path,
    get_figures_path,
    get_millennium_path,
    get_logs_path,
    get_state_path,
    load_config,
    set_random_seed,
    get_random_seed,
    _random_seed
)


class TestPathConstants:
    """Tests for path constant functions."""

    def test_get_project_root_exists(self):
        """Test that project root is a valid path."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_get_data_raw_path(self):
        """Test that raw data path is correctly constructed."""
        raw_path = get_data_raw_path()
        expected = get_project_root() / "data" / "raw"
        assert raw_path == expected

    def test_get_data_processed_path(self):
        """Test that processed data path is correctly constructed."""
        processed_path = get_data_processed_path()
        expected = get_project_root() / "data" / "processed"
        assert processed_path == expected

    def test_get_output_path(self):
        """Test that output path is correctly constructed."""
        output_path = get_output_path()
        expected = get_project_root() / "outputs"
        assert output_path == expected

    def test_get_figures_path(self):
        """Test that figures path is correctly constructed."""
        figures_path = get_figures_path()
        expected = get_output_path() / "figures"
        assert figures_path == expected

    def test_get_millennium_path(self):
        """Test that millennium path is correctly constructed."""
        millennium_path = get_millennium_path()
        expected = get_data_raw_path() / "millennium"
        assert millennium_path == expected

    def test_get_logs_path(self):
        """Test that logs path is correctly constructed."""
        logs_path = get_logs_path()
        expected = get_project_root() / "state" / "logs"
        assert logs_path == expected

    def test_get_state_path(self):
        """Test that state path is correctly constructed."""
        state_path = get_state_path()
        expected = get_project_root() / "state"
        assert state_path == expected


class TestRandomSeed:
    """Tests for random seed management."""

    def test_set_random_seed_updates_global(self):
        """Test that set_random_seed updates the global seed."""
        original_seed = get_random_seed()
        new_seed = 12345
        set_random_seed(new_seed)
        assert get_random_seed() == new_seed
        # Restore original
        set_random_seed(original_seed)

    def test_set_random_seed_affects_python_random(self):
        """Test that set_random_seed affects Python's random module."""
        set_random_seed(42)
        val1 = random.random()
        set_random_seed(42)
        val2 = random.random()
        assert val1 == val2
        # Restore original
        set_random_seed(42)

    def test_set_random_seed_affects_numpy_random(self):
        """Test that set_random_seed affects numpy's random module."""
        set_random_seed(42)
        val1 = np.random.random()
        set_random_seed(42)
        val2 = np.random.random()
        assert val1 == val2
        # Restore original
        set_random_seed(42)

    def test_get_random_seed_returns_int(self):
        """Test that get_random_seed returns an integer."""
        seed = get_random_seed()
        assert isinstance(seed, int)


class TestLoadConfig:
    """Tests for configuration loading."""

    def test_load_config_missing_file_returns_defaults(self):
        """Test that loading a missing config returns defaults."""
        config = load_config("nonexistent_config.yaml")
        assert isinstance(config, dict)
        assert "random_seed" in config
        assert config["random_seed"] == 42

    def test_load_config_default_location(self):
        """Test that load_config can load from default location if exists."""
        # This test passes if it doesn't crash; if config.yaml exists, it loads it.
        # If it doesn't exist, it returns defaults.
        config = load_config()
        assert isinstance(config, dict)

    def test_config_contains_expected_fields(self):
        """Test that default config contains expected fields."""
        config = load_config("nonexistent.yaml")
        expected_fields = [
            "random_seed",
            "tng_api_key",
            "chunk_size",
            "mass_tolerance",
            "binning_thresholds"
        ]
        for field in expected_fields:
            assert field in config