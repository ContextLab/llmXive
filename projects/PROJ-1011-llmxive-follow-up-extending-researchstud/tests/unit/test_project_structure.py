import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup_project_structure import main

class TestProjectStructure:
    """Tests for T001a: Project directory structure creation."""

    def test_directory_structure_creation(self, tmp_path):
        """
        Verify that the main function creates the required directory structure.
        
        This test creates a temporary directory to simulate the project root,
        runs the setup function, and asserts that all required directories exist.
        """
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the setup function
            # Note: The function uses Path.cwd() to determine root, 
            # so we don't pass arguments
            result = main()
            
            # Assert return code is 0 (success)
            assert result == 0, f"Setup function returned non-zero: {result}"
            
            # Verify required directories exist
            required_dirs = [
                "projects/PROJ-1011-llmxive-follow-up-extending-researchstud",
                "code",
                "data/raw",
                "data/processed",
                "data/results",
                "tests",
                "state",
                "docs",
                "figures"
            ]
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Required directory missing: {dir_name}"
                assert dir_path.is_dir(), f"Path is not a directory: {dir_name}"
                
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path):
        """
        Verify that running the setup function multiple times doesn't cause errors.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run setup twice
            result1 = main()
            result2 = main()
            
            assert result1 == 0
            assert result2 == 0
            
            # Verify directories still exist and are valid
            required_dirs = [
                "code",
                "data",
                "tests",
                "state"
            ]
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists() and dir_path.is_dir()
                
        finally:
            os.chdir(original_cwd)
