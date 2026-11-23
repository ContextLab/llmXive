"""
Tests for the code directory structure initialization.
"""
import os
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add the code directory to the path for imports
# Assuming tests are run from project root or tests/ subdirectory
project_root = Path(__file__).resolve().parent.parent.parent
code_dir_path = project_root / "code"
if str(code_dir_path) not in sys.path:
    sys.path.insert(0, str(code_dir_path))

from setup_code_structure import get_project_root, create_directories, verify_structure

class TestCodeStructure:
    """Test cases for code structure initialization."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """
        Setup and teardown for each test.
        Uses a temporary directory to avoid modifying the actual project structure during tests.
        """
        self.original_cwd = Path.cwd()
        self.temp_dir = tmp_path
        
        # Change to the temporary directory to simulate a project root
        os.chdir(self.temp_dir)
        
        # Create a fake requirements.txt to trick get_project_root into recognizing this as the root
        (self.temp_dir / "requirements.txt").touch()
        
        yield
        
        # Restore original working directory
        os.chdir(self.original_cwd)

    def test_get_project_root_finds_temp_dir(self):
        """Test that get_project_root correctly identifies the temporary directory as the project root."""
        root = get_project_root()
        assert root == self.temp_dir, f"Expected {self.temp_dir}, got {root}"

    def test_create_directories_creates_code_folder(self):
        """Test that create_directories successfully creates the 'code/' directory."""
        result = create_directories(self.temp_dir)
        assert result is True, "create_directories should return True on success"
        assert (self.temp_dir / "code").exists(), "The 'code/' directory should exist after creation"
        assert (self.temp_dir / "code").is_dir(), "The 'code/' path should be a directory"

    def test_create_directories_idempotent(self):
        """Test that calling create_directories multiple times is safe (idempotent)."""
        # First call
        result1 = create_directories(self.temp_dir)
        assert result1 is True
        
        # Second call (directory already exists)
        result2 = create_directories(self.temp_dir)
        assert result2 is True

    def test_verify_structure_passes_after_creation(self):
        """Test that verify_structure returns True after the directory is created."""
        # Create the directory first
        create_directories(self.temp_dir)
        
        # Verify
        result = verify_structure(self.temp_dir)
        assert result is True, "verify_structure should return True if directory exists"

    def test_verify_structure_fails_without_creation(self):
        """Test that verify_structure returns False if the directory does not exist."""
        # Ensure directory does not exist
        code_path = self.temp_dir / "code"
        if code_path.exists():
            shutil.rmtree(code_path)
        
        # Verify
        result = verify_structure(self.temp_dir)
        assert result is False, "verify_structure should return False if directory does not exist"

    def test_integration_workflow(self):
        """Test the full workflow: create then verify."""
        # Create
        create_result = create_directories(self.temp_dir)
        assert create_result is True
        
        # Verify
        verify_result = verify_structure(self.temp_dir)
        assert verify_result is True
        
        # Check actual existence
        assert (self.temp_dir / "code").exists()
        assert (self.temp_dir / "code").is_dir()
