"""
Unit tests for the setup_structure module (Task T001b).
Verifies that code directory hierarchy is created correctly and is writable.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
# We need to add the code directory to sys.path for import
import sys
from unittest.mock import patch

# Get the path to the code directory
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
code_dir = project_root / "code"

if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_structure import setup_code_directories, get_project_root, CODE_SUBDIRS


class TestSetupCodeDirectories:
    """Tests for the setup_code_directories function."""

    def test_creates_all_required_subdirs(self, tmp_path):
        """Test that all required subdirectories are created."""
        # Run the function
        result = setup_code_directories(tmp_path, verbose=False)
        
        # Check that all expected directories were created
        assert len(result) == len(CODE_SUBDIRS)
        
        for subdir_name in CODE_SUBDIRS:
            expected_path = tmp_path / "code" / subdir_name
            assert expected_path.exists(), f"Directory {expected_path} was not created"
            assert expected_path.is_dir(), f"{expected_path} is not a directory"

    def test_verifies_writability(self, tmp_path):
        """Test that the function verifies directories are writable."""
        # This should not raise an exception if directories are writable
        result = setup_code_directories(tmp_path, verbose=False)
        assert len(result) > 0

    def test_handles_existing_directories(self, tmp_path):
        """Test that the function handles pre-existing directories gracefully."""
        # Create a directory beforehand
        existing_dir = tmp_path / "code" / CODE_SUBDIRS[0]
        existing_dir.mkdir(parents=True)
        
        # Run the function - should not fail
        result = setup_code_directories(tmp_path, verbose=False)
        
        # Should still return the expected count
        assert len(result) == len(CODE_SUBDIRS)

    def test_creates_code_root_if_missing(self, tmp_path):
        """Test that the code root directory is created if it doesn't exist."""
        code_root = tmp_path / "code"
        assert not code_root.exists()
        
        result = setup_code_directories(tmp_path, verbose=False)
        
        assert code_root.exists()
        assert code_root.is_dir()

    def test_returns_absolute_paths(self, tmp_path):
        """Test that the function returns absolute paths."""
        result = setup_code_directories(tmp_path, verbose=False)
        
        for path in result:
            assert path.is_absolute(), f"Path {path} is not absolute"

    def test_unwritable_directory_raises_error(self, tmp_path):
        """Test that an unwritable directory raises an OSError."""
        # Create a directory and make it read-only
        code_root = tmp_path / "code"
        code_root.mkdir()
        
        # Create a subdirectory
        subdir = code_root / CODE_SUBDIRS[0]
        subdir.mkdir()
        
        # Make it read-only (simulate unwritable)
        # Note: This might not work on all systems (e.g., Windows, some Linux configs)
        # but we can test the logic by mocking
        original_mkdir = Path.mkdir
        
        def mock_mkdir_fail(self, *args, **kwargs):
            if self.name == CODE_SUBDIRS[1]:  # Fail on second subdir
                raise PermissionError("Simulated permission error")
            return original_mkdir(self, *args, **kwargs)
        
        with patch.object(Path, 'mkdir', side_effect=mock_mkdir_fail):
            with pytest.raises(OSError) as exc_info:
                setup_code_directories(tmp_path, verbose=False)
            
            assert "Failed to create directory" in str(exc_info.value)

class TestGetProjectRoot:
    """Tests for the get_project_root function."""

    def test_returns_path_object(self):
        """Test that get_project_root returns a Path object."""
        result = get_project_root()
        assert isinstance(result, Path)

    def test_returns_existing_directory(self):
        """Test that get_project_root returns an existing directory."""
        result = get_project_root()
        assert result.exists()
        assert result.is_dir()