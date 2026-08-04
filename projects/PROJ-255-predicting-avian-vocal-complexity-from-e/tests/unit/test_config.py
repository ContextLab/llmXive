import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the functions to test
from src.utils.config import (
    get_project_root,
    get_data_dir,
    get_raw_data_dir,
    get_interim_data_dir,
    get_processed_data_dir,
    get_figures_dir,
    ensure_directories
)


class TestProjectRoot:
    """Tests for get_project_root function."""

    def test_returns_path_object(self):
        """Test that get_project_root returns a Path object."""
        root = get_project_root()
        assert isinstance(root, Path)

    def test_root_exists(self):
        """Test that the returned root path exists on the filesystem."""
        root = get_project_root()
        assert root.exists()

    def test_root_is_absolute(self):
        """Test that the returned root path is absolute."""
        root = get_project_root()
        assert root.is_absolute()


class TestDataDirectories:
    """Tests for directory getter functions."""

    def test_get_data_dir_returns_path(self):
        """Test that get_data_dir returns a Path object."""
        data_dir = get_data_dir()
        assert isinstance(data_dir, Path)

    def test_get_raw_data_dir_returns_path(self):
        """Test that get_raw_data_dir returns a Path object."""
        raw_dir = get_raw_data_dir()
        assert isinstance(raw_dir, Path)

    def test_get_interim_data_dir_returns_path(self):
        """Test that get_interim_data_dir returns a Path object."""
        interim_dir = get_interim_data_dir()
        assert isinstance(interim_dir, Path)

    def test_get_processed_data_dir_returns_path(self):
        """Test that get_processed_data_dir returns a Path object."""
        processed_dir = get_processed_data_dir()
        assert isinstance(processed_dir, Path)

    def test_get_figures_dir_returns_path(self):
        """Test that get_figures_dir returns a Path object."""
        fig_dir = get_figures_dir()
        assert isinstance(fig_dir, Path)

    def test_directory_hierarchy_correct(self):
        """Test that data directories are subdirectories of the project root."""
        root = get_project_root()
        data_dir = get_data_dir()
        raw_dir = get_raw_data_dir()
        interim_dir = get_interim_data_dir()
        processed_dir = get_processed_data_dir()
        fig_dir = get_figures_dir()

        # All data dirs should be under the project root
        assert str(data_dir).startswith(str(root))
        assert str(raw_dir).startswith(str(data_dir))
        assert str(interim_dir).startswith(str(data_dir))
        assert str(processed_dir).startswith(str(data_dir))
        assert str(fig_dir).startswith(str(data_dir))


class TestEnsureDirectories:
    """Tests for ensure_directories function."""

    def test_creates_all_standard_directories(self):
        """Test that ensure_directories creates all required directories."""
        # Use a temporary directory to test directory creation without side effects
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override the project root for testing
            original_root_func = get_project_root
            
            # Mock get_project_root to return our temp directory
            import src.utils.config as config_module
            
            def mock_get_project_root():
                return Path(tmpdir)
            
            config_module.get_project_root = mock_get_project_root
            
            try:
                # Call the function
                ensure_directories()
                
                # Verify directories were created
                data_dir = get_data_dir()
                raw_dir = get_raw_data_dir()
                interim_dir = get_interim_data_dir()
                processed_dir = get_processed_data_dir()
                fig_dir = get_figures_dir()
                
                assert data_dir.exists()
                assert data_dir.is_dir()
                assert raw_dir.exists()
                assert raw_dir.is_dir()
                assert interim_dir.exists()
                assert interim_dir.is_dir()
                assert processed_dir.exists()
                assert processed_dir.is_dir()
                assert fig_dir.exists()
                assert fig_dir.is_dir()
            finally:
                # Restore original function
                config_module.get_project_root = original_root_func

    def test_idempotent(self):
        """Test that calling ensure_directories multiple times is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import src.utils.config as config_module
            
            def mock_get_project_root():
                return Path(tmpdir)
            
            original_root_func = config_module.get_project_root
            config_module.get_project_root = mock_get_project_root
            
            try:
                # Call twice
                ensure_directories()
                ensure_directories()
                
                # Should still exist
                assert get_data_dir().exists()
                assert get_raw_data_dir().exists()
            finally:
                config_module.get_project_root = original_root_func

    def test_handles_existing_directories(self):
        """Test that ensure_directories doesn't fail if directories already exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import src.utils.config as config_module
            
            def mock_get_project_root():
                return Path(tmpdir)
            
            original_root_func = config_module.get_project_root
            config_module.get_project_root = mock_get_project_root
            
            try:
                # Create directories manually first
                ensure_directories()
                
                # Call again - should not raise
                ensure_directories()
                
                # Verify they still exist
                assert get_data_dir().exists()
            finally:
                config_module.get_project_root = original_root_func
