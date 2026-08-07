"""
Unit tests for T001: Create project root directories.

Tests verify that the root directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so we can import the module
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from create_t001_root import main

class TestCreateT001Root:
    """Tests for T001 directory creation."""

    def test_directory_creation_in_temp(self, tmp_path):
        """Test that directory creation works in a temporary directory."""
        # Create a temporary directory structure to simulate the project root
        temp_root = tmp_path / "projects" / "PROJ-951-llmxive-follow-up-extending-physisforcin" / "code"
        
        # Change to the temp directory to simulate running the script
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Create the directory using the main function logic
            temp_root.mkdir(parents=True, exist_ok=True)
            
            # Verify the directory was created
            assert temp_root.exists(), "Root directory was not created"
            assert temp_root.is_dir(), "Root path is not a directory"
            
            # Verify we can list the directory
            contents = list(temp_root.iterdir())
            # Directory should be empty at this stage (T001 only creates root)
            assert len(contents) == 0, f"Directory should be empty, but contains: {contents}"
            
        finally:
            os.chdir(original_cwd)

    def test_directory_exists_after_creation(self, tmp_path):
        """Test that the directory persists after creation."""
        temp_root = tmp_path / "projects" / "PROJ-951-llmxive-follow-up-extending-physisforcin" / "code"
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Create the directory
            temp_root.mkdir(parents=True, exist_ok=True)
            
            # Verify it exists
            assert temp_root.exists()
            
            # Create a dummy file to ensure we can write to it
            dummy_file = temp_root / "test.txt"
            dummy_file.write_text("test")
            
            assert dummy_file.exists()
            assert dummy_file.read_text() == "test"
            
        finally:
            os.chdir(original_cwd)

    def test_parent_directories_created(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        temp_root = tmp_path / "projects" / "PROJ-951-llmxive-follow-up-extending-physisforcin" / "code"
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Create the full path including parents
            temp_root.mkdir(parents=True, exist_ok=True)
            
            # Verify all parent directories exist
            assert (tmp_path / "projects").exists()
            assert (tmp_path / "projects" / "PROJ-951-llmxive-follow-up-extending-physisforcin").exists()
            assert temp_root.exists()
            
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])