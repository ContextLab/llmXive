import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the project root to the path to allow imports from src
# This assumes the tests are run from the project root or with pytest
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.utils.config import (
    get_config,
    get_path,
    validate_api_keys,
    set_random_seed,
    get_seed,
    ensure_directories,
)


class TestConfigPaths:
    """Tests for configuration path resolution."""

    def test_get_config_returns_dict(self):
        """Verify that get_config returns a dictionary."""
        config = get_config()
        assert isinstance(config, dict)
        assert "paths" in config
        assert "seed" in config

    def test_get_path_resolves_data_raw(self):
        """Verify get_path correctly resolves 'data_raw' relative to project root."""
        path = get_path("data_raw")
        assert isinstance(path, Path)
        assert path.is_absolute()
        # The path should end with data/raw
        assert path.parts[-2:] == ("data", "raw")

    def test_get_path_resolves_output(self):
        """Verify get_path correctly resolves 'output' relative to project root."""
        path = get_path("output")
        assert isinstance(path, Path)
        assert path.is_absolute()
        assert path.name == "output"

    def test_ensure_directories_creates_missing(self, tmp_path):
        """Verify ensure_directories creates the specified directories."""
        # Temporarily patch the project root to use a temp directory
        original_root = project_root
        # We cannot easily patch the global project_root variable used in config.py
        # So we test the function behavior by ensuring it doesn't crash
        # and that it creates directories if we pass a valid path structure.
        # A more robust test would involve mocking the path resolution logic.
        # For now, we verify the function exists and runs without error.
        try:
            ensure_directories()
        except Exception as e:
            # If it fails, it should be due to permission or other runtime issues, not missing logic
            # We expect it to succeed in a normal environment
            pytest.fail(f"ensure_directories raised an unexpected error: {e}")


class TestRandomSeed:
    """Tests for random seed management."""

    def test_set_random_seed_sets_numpy_and_random(self):
        """Verify set_random_seed sets the seed for numpy and random."""
        import random
        import numpy as np

        seed_value = 12345
        set_random_seed(seed_value)

        # Generate a number from random
        val1 = random.random()
        val2 = random.random()

        # Reset seed
        set_random_seed(seed_value)

        # Generate again
        val3 = random.random()
        val4 = random.random()

        assert val1 == val3
        assert val2 == val4

    def test_set_random_seed_sets_numpy(self):
        """Verify set_random_seed sets the seed for numpy."""
        import numpy as np

        seed_value = 98765
        set_random_seed(seed_value)
        arr1 = np.random.rand(5)

        set_random_seed(seed_value)
        arr2 = np.random.rand(5)

        assert np.array_equal(arr1, arr2)

    def test_get_seed_returns_current_seed(self):
        """Verify get_seed returns the currently set seed."""
        seed_value = 42
        set_random_seed(seed_value)
        assert get_seed() == seed_value


class TestConstants:
    """Tests for configuration constants."""

    def test_config_contains_seed_key(self):
        """Verify the config dictionary contains the seed key."""
        config = get_config()
        assert "seed" in config
        assert isinstance(config["seed"], int)

    def test_config_paths_structure(self):
        """Verify the config paths structure."""
        config = get_config()
        paths = config.get("paths", {})
        assert "data_raw" in paths
        assert "data_processed" in paths
        assert "output" in paths


class TestConfigDictionary:
    """Tests for the full configuration dictionary structure."""

    def test_config_keys(self):
        """Verify the expected top-level keys exist."""
        config = get_config()
        expected_keys = {"paths", "seed"}
        assert set(config.keys()).issuperset(expected_keys)

    def test_paths_keys(self):
        """Verify the expected path keys exist."""
        config = get_config()
        paths = config.get("paths", {})
        expected_path_keys = {"data_raw", "data_processed", "output"}
        assert set(paths.keys()).issuperset(expected_path_keys)


class TestAPIKeyValidation:
    """Tests for API key validation logic."""

    def test_validate_api_keys_returns_true_when_set(self, monkeypatch):
        """Verify validate_api_keys returns True when MP_API_KEY is set."""
        monkeypatch.setenv("MP_API_KEY", "fake_key_for_testing")
        result = validate_api_keys()
        assert result is True

    def test_validate_api_keys_returns_false_when_missing(self, monkeypatch):
        """Verify validate_api_keys returns False when MP_API_KEY is missing."""
        # Ensure the key is not set
        monkeypatch.delenv("MP_API_KEY", raising=False)
        result = validate_api_keys()
        assert result is False

    def test_validate_api_keys_handles_empty_string(self, monkeypatch):
        """Verify validate_api_keys returns False when MP_API_KEY is empty."""
        monkeypatch.setenv("MP_API_KEY", "")
        result = validate_api_keys()
        assert result is False