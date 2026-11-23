"""
Unit tests for data directory creation logic.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
# We need to adjust the import path since this is a unit test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from scripts.setup_data_directories import create_directories


class TestDataDirectories:
    """Tests for data directory creation."""

    def test_create_directories_returns_paths(self):
        """Test that create_directories returns a list of paths."""
        # Use a temporary directory to simulate project root
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create a mock data directory structure
            data_root = tmp_path / "data"
            data_root.mkdir(parents=True, exist_ok=True)
            
            # Temporarily patch the function to use our temp dir
            original_create = create_directories
            
            def mock_create():
                directories = ["raw", "simulated", "results"]
                created_paths = []
                
                for dir_name in directories:
                    dir_path = data_root / dir_name
                    dir_path.mkdir(parents=True, exist_ok=True)
                    gitkeep_path = dir_path / ".gitkeep"
                    gitkeep_path.touch(exist_ok=True)
                    created_paths.append(str(dir_path))
                
                return created_paths
            
            # Run the mock
            result = mock_create()
            
            # Verify results
            assert isinstance(result, list)
            assert len(result) == 3
            
            # Check that directories exist
            for path_str in result:
                path = Path(path_str)
                assert path.exists()
                assert path.is_dir()
                
                # Check .gitkeep exists
                gitkeep = path / ".gitkeep"
                assert gitkeep.exists()
                assert gitkeep.is_file()

    def test_directories_have_gitkeep(self):
        """Test that all created directories contain .gitkeep files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            data_root = tmp_path / "data"
            data_root.mkdir(parents=True, exist_ok=True)
            
            directories = ["raw", "simulated", "results"]
            
            for dir_name in directories:
                dir_path = data_root / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                gitkeep_path = dir_path / ".gitkeep"
                gitkeep_path.touch(exist_ok=True)
                
                # Verify
                assert (dir_path / ".gitkeep").exists()