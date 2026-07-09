"""
Unit tests for code/config.py
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
import yaml

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import Config, get_event_window_days, get_random_seed, config


class TestConfigDefaults:
    """Test that default configuration values are set correctly."""

    def test_project_root_is_path(self):
        """Project root should be a Path object."""
        assert isinstance(config.get("paths.project_root"), Path)

    def test_event_window_days_default(self):
        """Default event window should be 30 days."""
        assert config.get("analysis.event_window_days") == 30

    def test_control_window_days_default(self):
        """Default control window should be 30 days."""
        assert config.get("analysis.control_window_days") == 30

    def test_random_seed_default(self):
        """Default random seed should be 42."""
        assert config.get("random_seed") == 42

    def test_min_magnitude_default(self):
        """Default minimum magnitude should be 4.0."""
        assert config.get("analysis.min_magnitude") == 4.0

    def test_max_depth_km_default(self):
        """Default max depth should be 70 km."""
        assert config.get("analysis.max_depth_km") == 70

    def test_usgs_base_url_default(self):
        """Default USGS base URL should be correct."""
        expected = "https://earthquake.usgs.gov/fdsnws/event/1/query"
        assert config.get("usgs.base_url") == expected

    def test_paths_exist(self):
        """All configured paths should exist as directories."""
        paths_to_check = [
            "paths.data_raw",
            "paths.data_interim",
            "paths.data_processed",
            "paths.data_figures",
            "paths.contracts",
            "paths.docs"
        ]
        for path_key in paths_to_check:
            path = config.get(path_key)
            assert path.exists(), f"Path {path_key} does not exist: {path}"


class TestConfigOverride:
    """Test that configuration can be overridden via YAML."""

    def test_yaml_override(self, tmp_path):
        """Test that values from config.yaml override defaults."""
        # Create a temporary config file
        override_config = {
            "analysis": {
                "event_window_days": 45,
                "min_magnitude": 5.0
            },
            "random_seed": 123
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(override_config, f)
        
        # We need to simulate a new Config instance with this file
        # Since the singleton is already loaded, we test the logic manually
        # by creating a new Config object with a modified _CONFIG_FILE path
        # For this test, we just verify the override mechanism exists
        
        # Note: In a real scenario, we would mock the _CONFIG_FILE path
        # or reload the module. For now, we test the _merge_dict logic.
        config_instance = Config()
        config_instance._merge_dict(
            config_instance._data, 
            override_config
        )
        
        assert config_instance.get("analysis.event_window_days") == 45
        assert config_instance.get("analysis.min_magnitude") == 5.0
        assert config_instance.get("random_seed") == 123


class TestConvenienceFunctions:
    """Test the convenience accessor functions."""

    def test_get_event_window_days(self):
        """get_event_window_days should return the correct value."""
        assert get_event_window_days() == 30

    def test_get_random_seed(self):
        """get_random_seed should return the correct value."""
        assert get_random_seed() == 42

    def test_get_min_magnitude(self):
        """get_min_magnitude should return the correct value."""
        assert get_min_magnitude() == 4.0


class TestPathResolution:
    """Test that relative paths are correctly resolved to absolute paths."""

    def test_relative_to_absolute(self):
        """Relative paths should be resolved relative to project root."""
        root = config.get("paths.project_root")
        raw_path = config.get("paths.data_raw")
        
        # raw_path should be root / "data/raw"
        expected = root / "data/raw"
        assert raw_path == expected
        assert raw_path.is_absolute()


class TestConfigGet:
    """Test the generic get method."""

    def test_get_nested_value(self):
        """Should retrieve nested values using dot notation."""
        assert config.get("analysis.event_window_days") == 30
        assert config.get("usgs.base_url") is not None

    def test_get_missing_key(self):
        """Should return default for missing keys."""
        assert config.get("nonexistent.key", "default") == "default"
        assert config.get("nonexistent.key") is None
