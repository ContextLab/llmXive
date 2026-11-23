"""
Unit tests for src.utils.config module.

Verifies configuration loading, path resolution, seed reproducibility,
and API key validation.
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys
from unittest.mock import patch

# Ensure the project root is in the path for imports
# Adjust based on actual project structure if needed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.config import (
    get_config,
    get_path,
    validate_api_keys,
    set_random_seed,
    get_seed,
    ensure_directories,
    DEFAULT_SEED,
    _PROJECT_ROOT,
)
import random
import numpy as np

class TestConfigPaths:
    """Tests for path configuration and resolution."""

    def test_get_config_returns_root(self):
        """Verify get_config returns the project root."""
        config = get_config()
        assert "root" in config
        assert isinstance(config["root"], Path)

    def test_get_config_contains_paths(self):
        """Verify get_config contains expected path keys."""
        config = get_config()
        assert "paths" in config
        expected_keys = ["data_raw", "data_processed", "output", "figures", "models", "specs"]
        for key in expected_keys:
            assert key in config["paths"], f"Missing path key: {key}"

    def test_get_path_resolves_correctly(self):
        """Verify get_path returns absolute paths relative to project root."""
        # We don't know the exact root in a test environment, so we check type and structure
        path = get_path("data_raw")
        assert isinstance(path, Path)
        assert path.is_absolute()

    def test_get_path_raises_on_invalid_key(self):
        """Verify get_path raises KeyError for unknown keys."""
        with pytest.raises(KeyError):
            get_path("invalid_key")

    def test_get_path_with_relative(self):
        """Verify get_path appends relative paths correctly."""
        base = get_path("output")
        full = get_path("output", relative=Path("test.txt"))
        assert full == base / "test.txt"

class TestRandomSeed:
    """Tests for random seed management."""

    def test_get_seed_returns_default(self):
        """Verify get_seed returns the default seed (42)."""
        assert get_seed() == 42

    def test_set_random_seed_sets_random(self):
        """Verify set_random_seed affects the random module."""
        set_random_seed(123)
        val1 = random.random()
        
        set_random_seed(123)
        val2 = random.random()
        
        assert val1 == val2

    def test_set_random_seed_sets_numpy(self):
        """Verify set_random_seed affects numpy."""
        set_random_seed(456)
        arr1 = np.random.rand(10)
        
        set_random_seed(456)
        arr2 = np.random.rand(10)
        
        assert np.array_equal(arr1, arr2)

    def test_set_random_seed_default(self):
        """Verify set_random_seed with no args uses default seed."""
        set_random_seed()
        val1 = random.random()
        
        set_random_seed()
        val2 = random.random()
        
        assert val1 == val2

class TestConstants:
    """Tests for physical constants configuration."""

    def test_config_contains_constants(self):
        """Verify get_config includes constants."""
        config = get_config()
        assert "constants" in config
        assert "anisotropy_lower_bound" in config["constants"]
        assert "anisotropy_upper_bound" in config["constants"]

    def test_constants_have_expected_values(self):
        """Verify constants have the expected numeric values."""
        constants = get_config()["constants"]
        assert constants["anisotropy_lower_bound"] == 0.0
        assert constants["anisotropy_upper_bound"] == 3.0

class TestConfigDictionary:
    """Tests for the structure of the configuration dictionary."""

    def test_config_structure(self):
        """Verify the overall structure of the config dictionary."""
        config = get_config()
        assert isinstance(config, dict)
        assert "root" in config
        assert "seed" in config
        assert "paths" in config
        assert "constants" in config

    def test_paths_are_paths(self):
        """Verify all path values in config are Path objects."""
        config = get_config()
        for key, path in config["paths"].items():
            assert isinstance(path, Path), f"Path for {key} is not a Path object"

class TestAPIKeyValidation:
    """Tests for API key validation logic."""

    def test_validate_api_keys_passes_when_set(self):
        """Verify validation passes when MP_API_KEY is set."""
        with patch.dict(os.environ, {"MP_API_KEY": "fake_key"}):
            # Should not raise
            validate_api_keys()

    def test_validate_api_keys_fails_when_missing(self):
        """Verify validation raises ValueError when MP_API_KEY is missing."""
        # Ensure it's not set
        env = os.environ.copy()
        env.pop("MP_API_KEY", None)
        
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="Missing required API keys"):
                validate_api_keys()

class TestEnsureDirectories:
    """Tests for directory creation."""

    def test_ensure_directories_creates_folders(self, tmp_path):
        """Verify ensure_directories creates the required folder structure."""
        # Temporarily override the project root for testing
        original_root = _PROJECT_ROOT
        
        # We need to mock the _get_project_root function or the module behavior
        # Since _PROJECT_ROOT is a module-level constant, we patch the function that uses it
        # or we test the side effect on a known temp path if the module allowed it.
        # For this test, we assume the module logic works on the real FS or we mock it.
        # A simpler approach: test that the function exists and doesn't crash on a temp dir mock.
        
        # Mocking the root resolution
        with patch('src.utils.config._PROJECT_ROOT', tmp_path):
            # We need to re-import or patch the function that uses _PROJECT_ROOT
            # Since _get_project_root returns the constant, we patch the constant usage
            # Actually, let's just check if the function runs without error
            # and creates the dirs in the temp path if we can trick it.
            pass
        
        # Alternative: Just verify the function exists and signature is correct
        # The actual creation depends on the environment.
        # Let's assume the real execution creates them.
        # We will test that the function is callable.
        assert callable(ensure_directories)

        # To actually test creation, we need to patch the root resolution logic.
        # Since _PROJECT_ROOT is a constant, we can't easily change it without reloading the module.
        # Instead, we verify the logic by checking if the function calls mkdir.
        with patch('src.utils.config._PROJECT_ROOT', tmp_path):
            # We need to reload the module to pick up the patched constant?
            # Or just trust the logic. Let's try to patch the function that returns root.
            pass

        # Robust test:
        # Create a temp dir, patch the module's _get_project_root to return it.
        # Then call ensure_directories and check if dirs exist.
        # Since _PROJECT_ROOT is a constant, we patch the function that accesses it.
        
        # Re-defining the check locally to avoid module reload issues in test
        def mock_get_root():
            return tmp_path
        
        with patch.object(sys.modules['src.utils.config'], '_get_project_root', mock_get_root):
            # We also need to patch the global _PROJECT_ROOT if it's used directly
            # The code uses _PROJECT_ROOT directly in get_path and ensure_directories
            # So we must patch the module's namespace
            with patch('src.utils.config._PROJECT_ROOT', tmp_path):
                ensure_directories()
                
                # Check if at least one expected directory exists
                data_raw = tmp_path / "data/raw"
                assert data_raw.exists()

    def test_ensure_directories_handles_existing(self):
        """Verify ensure_directories does not crash if directories already exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            with patch('src.utils.config._PROJECT_ROOT', tmp_path):
                ensure_directories()
                # Run twice
                ensure_directories()
                assert (tmp_path / "data/raw").exists()