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
    get_constants,
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


class TestEnsureDirectories:
    """Tests for directory creation logic."""

    def test_ensure_directories_creates_missing_dirs(self, tmp_path):
        """Verify ensure_directories creates directories that do not exist."""
        # Mock the get_path function to return tmp_path subdirectories
        test_data_raw = tmp_path / "data" / "raw"
        test_data_processed = tmp_path / "data" / "processed"
        test_output = tmp_path / "output"

        # Ensure they don't exist yet
        assert not test_data_raw.exists()
        assert not test_data_processed.exists()
        assert not test_output.exists()

        # Call ensure_directories with mocked paths
        # We patch get_path to return our tmp_path locations for specific keys
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("src.utils.config.get_path", lambda key: {
                "data_raw": test_data_raw,
                "data_processed": test_data_processed,
                "output": test_output
            }.get(key, tmp_path))
            
            # Note: ensure_directories internally calls get_path, so we patch there
            # However, since ensure_directories is in the same module, we need to patch the module it imports from
            # A simpler approach for this test is to patch inside the function or use a different strategy.
            # Let's rely on the fact that ensure_directories uses get_path.
            # We will patch get_path in the config module.
            
            # Re-import to ensure we are patching the right place if needed, 
            # but typically patching the name used by the function is key.
            from src.utils import config
            
            # Patch get_path within the config module namespace
            original_get_path = config.get_path
            config.get_path = lambda key: {
                "data_raw": test_data_raw,
                "data_processed": test_data_processed,
                "output": test_output
            }.get(key, tmp_path)

            try:
                config.ensure_directories()
            finally:
                config.get_path = original_get_path

        assert test_data_raw.exists()
        assert test_data_processed.exists()
        assert test_output.exists()
        assert test_data_raw.is_dir()
        assert test_data_processed.is_dir()
        assert test_output.is_dir()


class TestGetConstants:
    """Tests for the get_constants function."""

    def test_get_constants_returns_dict(self):
        """Verify get_constants returns a dictionary."""
        constants = get_constants()
        assert isinstance(constants, dict)
    
    def test_get_constants_contains_expected_keys(self):
        """Verify get_constants contains expected physical constants or project constants."""
        constants = get_constants()
        # The specific keys depend on implementation, but it should be non-empty and dict-like
        assert len(constants) > 0