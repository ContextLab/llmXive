"""
Tests for the directory structure setup script (Task T001b).
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import create_project_structure, get_project_paths


class TestDirectoryStructure:
    """Test cases for directory creation logic."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to simulate a project root."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_get_project_paths_returns_correct_structure(self, temp_project_root):
        """Verify that get_project_paths returns the expected relative paths."""
        # We need to mock the project root context or pass it if the function accepts it.
        # Assuming get_project_paths returns relative strings or paths relative to cwd.
        # For this test, we verify the existence of keys in the returned dict/list if applicable.
        # If get_project_paths relies on __file__ or cwd, we change cwd temporarily.
        
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root)
            paths = get_project_paths()
            
            # Check that standard keys exist
            assert "code" in str(paths) or any("code" in str(p) for p in paths)
            assert "data" in str(paths) or any("data" in str(p) for p in paths)
        finally:
            os.chdir(original_cwd)

    def test_create_project_structure_creates_directories(self, temp_project_root):
        """Verify that create_project_structure actually creates the directories."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root)
            
            paths = get_project_paths()
            created_count = create_project_structure(paths)
            
            # Ensure at least some directories were created
            assert created_count > 0
            
            # Verify specific required paths from T001b
            required_subdirs = [
                "code",
                "data/raw",
                "data/processed",
                "output",
                "tests"
            ]
            
            for subdir in required_subdirs:
                target_path = temp_project_root / subdir
                assert target_path.exists(), f"Directory {subdir} was not created."
                assert target_path.is_dir(), f"Path {subdir} exists but is not a directory."
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, temp_project_root):
        """Verify that running the script twice does not raise errors."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root)
            
            paths = get_project_paths()
            # First run
            count1 = create_project_structure(paths)
            # Second run
            count2 = create_project_structure(paths)
            
            # Second run might return 0 if nothing new was created, or same count if it overwrites
            # The key is that it doesn't crash.
            assert count2 >= 0
        finally:
            os.chdir(original_cwd)