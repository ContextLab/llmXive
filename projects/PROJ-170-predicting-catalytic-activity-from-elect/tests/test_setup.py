"""
Tests for the project setup script.
Verifies that all required directories are created.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the setup logic
import sys
from pathlib import Path

# Add parent directory to path to import setup_project
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from code.setup_project import PROJECT_DIRS, create_directories


class TestProjectSetup:
    """Test cases for project directory creation."""

    def test_directory_list_defined(self):
        """Test that PROJECT_DIRS is defined and contains expected entries."""
        assert isinstance(PROJECT_DIRS, list)
        assert len(PROJECT_DIRS) > 0
        assert "data/raw" in PROJECT_DIRS
        assert "data/processed" in PROJECT_DIRS
        assert "code" in PROJECT_DIRS
        assert "outputs" in PROJECT_DIRS
        assert "tests" in PROJECT_DIRS
        assert "state/projects" in PROJECT_DIRS
        assert "code/models" in PROJECT_DIRS

    def test_create_directories_in_temp(self):
        """Test directory creation in a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Temporarily change the working directory for the test
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                created, skipped = create_directories()
                
                # Verify all expected directories were created
                for dir_path in PROJECT_DIRS:
                    full_path = tmp_path / dir_path
                    assert full_path.exists(), f"Directory {full_path} was not created"
                    assert full_path.is_dir(), f"{full_path} exists but is not a directory"
                
                # In a fresh temp dir, all should be created
                assert len(created) == len(PROJECT_DIRS)
                assert len(skipped) == 0
            finally:
                os.chdir(original_cwd)

    def test_create_directories_idempotent(self):
        """Test that running create_directories twice doesn't fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # First run
                created1, skipped1 = create_directories()
                
                # Second run - should skip all
                created2, skipped2 = create_directories()
                
                assert len(created2) == 0, "Second run should not create any directories"
                assert len(skipped2) == len(PROJECT_DIRS)
            finally:
                os.chdir(original_cwd)