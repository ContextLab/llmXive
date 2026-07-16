"""
Unit tests for the project structure setup script.
Verifies that all required directories are created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so we can import setup_structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_structure import main


class TestSetupStructure:
    """Test cases for the project structure setup."""

    def test_all_directories_created(self, tmp_path):
        """Verify that all required directories are created."""
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run the setup
            result = main()
            
            # Check return code
            assert result == 0, "Setup should return 0 on success"
            
            # Verify each required directory exists
            required_dirs = [
                "data/raw",
                "data/processed",
                "data/analysis",
                "code",
                "tests/unit",
                "tests/integration",
                "docs",
                "specs"
            ]
            
            for dir_path in required_dirs:
                full_path = tmp_path / dir_path
                assert full_path.exists(), f"Directory {dir_path} should exist"
                assert full_path.is_dir(), f"{dir_path} should be a directory"
        
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def test_gitkeep_files_created(self, tmp_path):
        """Verify that .gitkeep files are created in each directory."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            main()
            
            required_dirs = [
                "data/raw",
                "data/processed",
                "data/analysis",
                "code",
                "tests/unit",
                "tests/integration",
                "docs",
                "specs"
            ]
            
            for dir_path in required_dirs:
                gitkeep_path = tmp_path / dir_path / ".gitkeep"
                assert gitkeep_path.exists(), f".gitkeep should exist in {dir_path}"
                assert gitkeep_path.is_file(), f".gitkeep in {dir_path} should be a file"
        
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path):
        """Verify that running setup twice doesn't cause errors."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run setup twice
            result1 = main()
            result2 = main()
            
            assert result1 == 0, "First run should succeed"
            assert result2 == 0, "Second run should succeed"
            
            # Verify directories still exist
            required_dirs = [
                "data/raw",
                "data/processed",
                "data/analysis",
                "code",
                "tests/unit",
                "tests/integration",
                "docs",
                "specs"
            ]
            
            for dir_path in required_dirs:
                full_path = tmp_path / dir_path
                assert full_path.exists(), f"Directory {dir_path} should still exist after second run"
        
        finally:
            os.chdir(original_cwd)