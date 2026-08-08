"""
Unit tests for the project setup script.
Verifies that the required directory structure is created correctly.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil
import sys

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_project import main

class TestProjectSetup:
    """Tests for the project setup functionality."""

    def test_directories_created(self, tmp_path):
        """Test that all required directories are created."""
        # Change to a temporary directory to avoid polluting the actual project
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run the setup
            result = main()
            
            # Check return code
            assert result == 0, "Setup script should return 0 on success"
            
            # Verify each required directory exists
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/analysis",
                "models",
                "analysis",
                "tests",
                "docs"
            ]
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def test_nested_directories_created(self, tmp_path):
        """Test that nested directories (e.g., data/raw) are created correctly."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = main()
            assert result == 0
            
            # Check specific nested paths
            nested_dirs = [
                "data/raw",
                "data/processed",
                "data/analysis"
            ]
            
            for dir_name in nested_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Nested directory {dir_name} was not created"
        finally:
            os.chdir(original_cwd)

    def test_setup_idempotent(self, tmp_path):
        """Test that running setup twice doesn't cause errors."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run setup first time
            result1 = main()
            assert result1 == 0
            
            # Run setup second time
            result2 = main()
            assert result2 == 0
            
            # Verify directories still exist
            required_dirs = ["code", "models", "analysis", "tests", "docs"]
            for dir_name in required_dirs:
                assert (tmp_path / dir_name).exists()
        finally:
            os.chdir(original_cwd)