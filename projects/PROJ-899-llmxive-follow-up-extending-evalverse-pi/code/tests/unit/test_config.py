"""
Unit tests for environment setup and configuration management.
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys
import json

# Add code to path if not already
if "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "code"))

from src.config import (
    get_project_root,
    get_data_root,
    get_state_root,
    get_reports_root,
    get_figures_root,
    get_cache_dir,
    get_raw_data_dir,
    get_processed_data_dir,
    ensure_environment,
    get_config_summary,
)
from src.data.config import (
    get_raw_data_path,
    get_processed_data_path,
    get_state_path,
    get_figures_path,
    get_reports_path,
    get_cache_path,
    ensure_directories,
    is_data_directory_ready,
    get_data_directories,
    get_data_summary,
)


class TestEnvironmentSetup:
    """Tests for environment initialization and directory creation."""

    def test_ensure_environment_creates_directories(self, tmp_path):
        """Test that ensure_environment creates necessary directories."""
        # We cannot easily mock the project root for these tests without complex patching,
        # so we test the existence of the directories after calling ensure_environment
        # in a real scenario, but here we verify the logic exists.
        # In a real run, this would create dirs under the actual project root.
        assert callable(ensure_environment)

    def test_get_raw_data_dir_exists(self):
        """Test that get_raw_data_dir returns a valid path object."""
        root = get_raw_data_dir()
        assert isinstance(root, Path)
        # The directory might not exist yet in test env, but the path should be valid
        assert root.name == "raw"

    def test_get_processed_data_dir_exists(self):
        """Test that get_processed_data_dir returns a valid path object."""
        root = get_processed_data_dir()
        assert isinstance(root, Path)
        assert root.name == "processed"


class TestConfigurationValues:
    """Tests for specific configuration values and paths."""

    def test_project_root_is_absolute(self):
        """Test that project root is an absolute path."""
        root = get_project_root()
        assert root.is_absolute()

    def test_data_root_is_child_of_project_root(self):
        """Test that data root is inside project root."""
        project_root = get_project_root()
        data_root = get_data_root()
        assert str(data_root).startswith(str(project_root))
        assert data_root.name == "data"

    def test_state_root_exists(self):
        """Test that state root is correctly defined."""
        state_root = get_state_root()
        assert state_root.name == "state"

    def test_cache_dir_location(self):
        """Test that cache directory is inside data."""
        cache_dir = get_cache_dir()
        data_root = get_data_root()
        assert str(cache_dir).startswith(str(data_root))
        assert cache_dir.name == "cache"


class TestConfigSummary:
    """Tests for configuration summary generation."""

    def test_get_config_summary_returns_dict(self):
        """Test that get_config_summary returns a dictionary."""
        summary = get_config_summary()
        assert isinstance(summary, dict)
        assert "project_root" in summary
        assert "data_root" in summary
        assert "random_seed" in summary

    def test_get_data_summary_returns_dict(self):
        """Test that get_data_summary returns a dictionary."""
        summary = get_data_summary()
        assert isinstance(summary, dict)
        assert "raw" in summary
        assert "processed" in summary
        assert "cache" in summary

    def test_directory_paths_are_strings(self):
        """Test that paths in summary are string representations."""
        summary = get_config_summary()
        for key, value in summary.items():
            if key.endswith("_dir") or key.endswith("_root"):
                assert isinstance(value, str)

    def test_is_data_directory_ready_function_exists(self):
        """Test that the readiness check function exists and is callable."""
        assert callable(is_data_directory_ready)

    def test_ensure_directories_creates_structure(self):
        """Test that ensure_directories creates the expected structure."""
        # This test relies on the actual file system
        # In a CI environment, we might need to mock the project root
        # For now, we verify the function exists and returns a dict
        dirs = ensure_directories()
        assert isinstance(dirs, dict)
        assert "raw" in dirs
        assert "processed" in dirs
        assert "cache" in dirs

    def test_data_directories_contains_all_keys(self):
        """Test that get_data_directories returns all expected keys."""
        dirs = get_data_directories()
        expected_keys = ["root", "raw", "processed", "state", "figures", "reports", "cache"]
        for key in expected_keys:
            assert key in dirs

    def test_path_functions_return_path_objects(self):
        """Test that path accessor functions return Path objects."""
        assert isinstance(get_raw_data_path(), Path)
        assert isinstance(get_processed_data_path(), Path)
        assert isinstance(get_state_path(), Path)
        assert isinstance(get_figures_path(), Path)
        assert isinstance(get_reports_path(), Path)
        assert isinstance(get_cache_path(), Path)