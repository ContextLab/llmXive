import os
import tempfile
from pathlib import Path
import pytest
import sys
import json

# Add code to path if not already there
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from src.config import (
    ensure_environment, 
    get_config_summary, 
    get_project_root, 
    get_data_root, 
    get_state_root, 
    get_reports_root, 
    get_figures_root, 
    get_raw_data_dir,
    get_processed_data_dir,
    get_cache_dir
)
from src.data.config import (
    get_data_directories, 
    get_raw_data_path, 
    get_processed_data_path, 
    get_state_path, 
    get_figures_path, 
    get_reports_path, 
    get_cache_path, 
    is_data_directory_ready,
    get_data_summary
)

class TestEnvironmentSetup:
    """Test environment configuration and directory creation."""

    def test_ensure_environment_creates_directories(self):
        """Test that ensure_environment creates all required directories."""
        # Use a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override get_project_root
            original_func = get_project_root
            
            def mock_get_project_root():
                return Path(tmpdir)
            
            # Monkey patch
            import src.config
            import src.data.config
            src.config.get_project_root = mock_get_project_root
            src.data.config.get_project_root = mock_get_project_root
            
            try:
                result = ensure_environment()
                assert result is True
                
                # Verify directories exist
                assert (Path(tmpdir) / "data").exists()
                assert (Path(tmpdir) / "data" / "raw").exists()
                assert (Path(tmpdir) / "data" / "processed").exists()
                assert (Path(tmpdir) / "data" / "state").exists()
                assert (Path(tmpdir) / "data" / "reports").exists()
                assert (Path(tmpdir) / "data" / "figures").exists()
                assert (Path(tmpdir) / "data" / "cache").exists()
            finally:
                # Restore original function
                src.config.get_project_root = original_func
                src.data.config.get_project_root = original_func

    def test_is_data_directory_ready(self):
        """Test that is_data_directory_ready returns True for valid setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_func = get_project_root
            
            def mock_get_project_root():
                return Path(tmpdir)
            
            import src.config
            import src.data.config
            src.config.get_project_root = mock_get_project_root
            src.data.config.get_project_root = mock_get_project_root
            
            try:
                # First ensure directories exist
                ensure_environment()
                result = is_data_directory_ready()
                assert result is True
            finally:
                src.config.get_project_root = original_func
                src.data.config.get_project_root = original_func

class TestConfigurationValues:
    """Test configuration value retrieval."""

    def test_get_project_root_returns_path(self):
        """Test that get_project_root returns a valid Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_get_data_root_returns_correct_path(self):
        """Test that get_data_root returns the correct data directory path."""
        root = get_project_root()
        data_root = get_data_root()
        expected = root / "data"
        assert data_root == expected

    def test_get_raw_data_dir_returns_correct_path(self):
        """Test that get_raw_data_dir returns the correct raw data path."""
        data_root = get_data_root()
        raw_dir = get_raw_data_dir()
        expected = data_root / "raw"
        assert raw_dir == expected

    def test_get_processed_data_dir_returns_correct_path(self):
        """Test that get_processed_data_dir returns the correct processed data path."""
        data_root = get_data_root()
        processed_dir = get_processed_data_dir()
        expected = data_root / "processed"
        assert processed_dir == expected

    def test_get_cache_dir_returns_correct_path(self):
        """Test that get_cache_dir returns the correct cache path."""
        data_root = get_data_root()
        cache_dir = get_cache_dir()
        expected = data_root / "cache"
        assert cache_dir == expected

class TestConfigSummary:
    """Test configuration summary functionality."""

    def test_get_config_summary_returns_dict(self):
        """Test that get_config_summary returns a dictionary."""
        summary = get_config_summary()
        assert isinstance(summary, dict)

    def test_get_config_summary_contains_project_info(self):
        """Test that get_config_summary contains project information."""
        summary = get_config_summary()
        assert "project_name" in summary
        assert "project_version" in summary
        assert "default_seed" in summary

    def test_get_config_summary_contains_paths(self):
        """Test that get_config_summary contains path information."""
        summary = get_config_summary()
        assert "paths" in summary
        assert "project_root" in summary["paths"]
        assert "data_root" in summary["paths"]

    def test_get_data_summary(self):
        """Test get_data_summary from data config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_func = get_project_root
            
            def mock_get_project_root():
                return Path(tmpdir)
            
            import src.config
            import src.data.config
            src.config.get_project_root = mock_get_project_root
            src.data.config.get_project_root = mock_get_project_root
            
            try:
                ensure_environment()
                summary = get_data_summary()
                assert isinstance(summary, dict)
                assert "raw" in summary
                assert "processed" in summary
                assert summary["raw"]["exists"] is True
            finally:
                src.config.get_project_root = original_func
                src.data.config.get_project_root = original_func
