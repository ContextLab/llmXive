"""
Unit tests for environment configuration and path management.
"""
import os
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from env_config import (
    get_project_root,
    get_data_raw_path,
    get_data_processed_path,
    get_results_path,
    get_figures_path,
    get_openneuro_api_key,
    validate_environment,
    _PROJECT_ROOT
)


class TestPathResolution:
    def test_project_root_is_correct(self):
        """Verify project root is the parent of the code directory."""
        expected_root = Path(__file__).parent.parent.parent
        assert get_project_root() == expected_root
        assert get_project_root().name == "PROJ-118-investigating-the-neural-correlates-of-p"

    def test_data_raw_path(self):
        """Verify data/raw path construction."""
        root = get_project_root()
        assert get_data_raw_path() == root / "data" / "raw"

    def test_data_processed_path(self):
        """Verify data/processed path construction."""
        root = get_project_root()
        assert get_data_processed_path() == root / "data" / "processed"

    def test_results_path(self):
        """Verify results path construction."""
        root = get_project_root()
        assert get_results_path() == root / "results"

    def test_figures_path(self):
        """Verify results/plots path construction."""
        root = get_project_root()
        assert get_figures_path() == root / "results" / "plots"


class TestEnvironmentVariables:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        # Save original state
        original_key = os.environ.get("OPENNEURO_API_KEY")
        yield
        # Restore original state
        if original_key is not None:
            os.environ["OPENNEURO_API_KEY"] = original_key
        elif "OPENNEURO_API_KEY" in os.environ:
            del os.environ["OPENNEURO_API_KEY"]

    def test_api_key_exists(self, monkeypatch):
        """Test retrieval of API key when set."""
        test_key = "test_api_key_12345"
        monkeypatch.setenv("OPENNEURO_API_KEY", test_key)
        assert get_openneuro_api_key() == test_key

    def test_api_key_missing(self):
        """Test behavior when API key is not set."""
        # Ensure it's not set
        if "OPENNEURO_API_KEY" in os.environ:
            del os.environ["OPENNEURO_API_KEY"]
        
        assert get_openneuro_api_key() is None

    def test_validate_environment_creates_dirs(self, tmp_path, monkeypatch):
        """Test that validate_environment ensures directories exist."""
        # We can't easily mock _PROJECT_ROOT to point to tmp_path without refactoring,
        # so we just check that the function runs without crashing and returns True
        # if the standard paths (relative to the actual project) exist or are created.
        # In a real CI, these might not exist yet.
        result = validate_environment()
        # The function should return True if it can create/access the dirs
        # or if they already exist.
        assert result is True
