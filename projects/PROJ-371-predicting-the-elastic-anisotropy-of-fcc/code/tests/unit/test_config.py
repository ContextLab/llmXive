"""
Unit tests for the configuration module (src/utils/config.py).

Tests verify:
- Configuration loading and path structure
- Random seed defaults and setters
- API key validation logic
- Path retrieval functionality
"""

import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
# Assuming the project structure is code/src/utils/config.py
# We need to adjust sys.path if running tests from the root
import sys
from pathlib import Path

# Add the 'code' directory to the path so we can import src.utils.config
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils import config


class TestConfigPaths:
    """Tests for path management in config."""

    def test_project_root_exists(self):
        """Verify that the project root is correctly identified."""
        assert config.PROJECT_ROOT.exists()
        assert config.PROJECT_ROOT.is_dir()

    def test_data_directories_exist(self):
        """Verify that required data directories exist."""
        assert config.DATA_RAW_DIR.exists()
        assert config.DATA_PROCESSED_DIR.exists()

    def test_output_directories_exist(self):
        """Verify that output directories exist."""
        assert config.OUTPUT_DIR.exists()
        assert config.FIGURES_DIR.exists()

    def test_get_path_valid_keys(self):
        """Test get_path with valid keys."""
        valid_keys = ["data_raw", "data_processed", "output", "figures"]
        for key in valid_keys:
            path = config.get_path(key)
            assert isinstance(path, Path)
            assert path.exists()

    def test_get_path_invalid_key(self):
        """Test get_path with an invalid key raises KeyError."""
        with pytest.raises(KeyError):
            config.get_path("invalid_key")


class TestRandomSeed:
    """Tests for random seed management."""

    def test_default_seed_is_42(self):
        """Verify the default random seed is 42."""
        assert config.get_seed() == 42

    def test_set_seed_updates_value(self):
        """Test that setting a seed updates the global value."""
        original_seed = config.get_seed()
        new_seed = 123
        config.set_random_seed(new_seed)
        assert config.get_seed() == new_seed
        # Restore original
        config.set_random_seed(original_seed)

    def test_set_seed_none_uses_default(self):
        """Test that setting seed to None uses the default (42)."""
        config.set_random_seed(999)
        config.set_random_seed(None)
        assert config.get_seed() == 42


class TestConstants:
    """Tests for constant values."""

    def test_anisotropy_bounds(self):
        """Verify anisotropy bounds are set correctly."""
        assert config.ANISOTROPY_LOWER_BOUND == 0.0
        assert config.ANISOTROPY_UPPER_BOUND == 3.0

    def test_min_unique_entries(self):
        """Verify minimum unique entries constant."""
        assert config.MIN_UNIQUE_ENTRIES == 50

    def test_outlier_std_devs(self):
        """Verify outlier standard deviations list."""
        assert config.OUTLIER_STD_DEVS == [2.5, 3.0, 3.5]

    def test_sensitivity_variance_threshold(self):
        """Verify sensitivity variance threshold."""
        assert config.SENSITIVITY_VARIANCE_THRESHOLD == 0.1


class TestConfigDictionary:
    """Tests for the CONFIG dictionary."""

    def test_config_has_paths(self):
        """Verify CONFIG contains paths."""
        cfg = config.get_config()
        assert "paths" in cfg
        assert "data_raw" in cfg["paths"]
        assert "data_processed" in cfg["paths"]

    def test_config_has_random_seed(self):
        """Verify CONFIG contains random seed."""
        cfg = config.get_config()
        assert "random_seed" in cfg
        assert cfg["random_seed"] == 42

    def test_config_has_constants(self):
        """Verify CONFIG contains constants."""
        cfg = config.get_config()
        assert "constants" in cfg
        assert "anisotropy_lower_bound" in cfg["constants"]

    def test_config_has_api_keys(self):
        """Verify CONFIG contains API key placeholders."""
        cfg = config.get_config()
        assert "api_keys" in cfg
        assert "materials_project" in cfg["api_keys"]


class TestAPIKeyValidation:
    """Tests for API key validation."""

    def test_validate_api_keys_missing(self, monkeypatch):
        """Test validation when API key is missing."""
        # Remove MP_API_KEY if it exists
        monkeypatch.delenv("MP_API_KEY", raising=False)
        # The function should return False and print a warning
        result = config.validate_api_keys()
        assert result is False

    def test_validate_api_keys_present(self, monkeypatch):
        """Test validation when API key is present."""
        monkeypatch.setenv("MP_API_KEY", "fake_key_for_testing")
        result = config.validate_api_keys()
        assert result is True