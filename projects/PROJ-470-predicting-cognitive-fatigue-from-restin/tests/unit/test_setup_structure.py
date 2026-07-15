"""
Unit tests for the project structure initialization (T001).
Verifies that the required directory hierarchy is created correctly.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add parent directory to path to import setup_structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_structure import main

class TestProjectStructure:
    """Tests for T001: Create project directory structure."""

    def test_directory_creation(self, tmp_path):
        """Test that all required directories are created."""
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Mock the base_dir logic by temporarily changing CWD
            # The script uses Path(".") which will be tmp_path
            
            # Run the main function (it will exit with 0 on success)
            # We need to capture the exit code or ensure no exception
            exit_code = main()
            
            assert exit_code == 0, "main() should return 0 on success"
            
            # Verify directories exist
            required_dirs = [
                "projects/PROJ-470-predicting-cognitive-fatigue-from-restin",
                "data/raw",
                "data/processed",
                "data/analysis",
                "code",
                "tests/unit",
                "tests/integration",
                "docs"
            ]
            
            for dir_path in required_dirs:
                full_path = tmp_path / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created"
                assert full_path.is_dir(), f"{dir_path} is not a directory"
                # Check for .gitkeep
                gitkeep = full_path / ".gitkeep"
                assert gitkeep.exists(), f".gitkeep missing in {dir_path}"
                
        finally:
            os.chdir(original_cwd)

    def test_nested_directory_structure(self, tmp_path):
        """Test that nested directories are created with parents."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            main()
            
            # Check nested structure
            nested_dirs = [
                "tests/unit",
                "tests/integration",
                "data/raw",
                "data/processed",
                "data/analysis"
            ]
            
            for dir_path in nested_dirs:
                full_path = tmp_path / dir_path
                assert full_path.exists(), f"Nested directory {dir_path} not created"
                # Verify parent exists
                assert full_path.parent.exists(), f"Parent of {dir_path} missing"
                
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path):
        """Test that running the script twice doesn't fail."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # First run
            exit_code_1 = main()
            assert exit_code_1 == 0
            
            # Second run (should skip existing)
            exit_code_2 = main()
            assert exit_code_2 == 0
            
            # Verify structure still intact
            required_dirs = [
                "projects/PROJ-470-predicting-cognitive-fatigue-from-restin",
                "data/raw",
                "code"
            ]
            
            for dir_path in required_dirs:
                full_path = tmp_path / dir_path
                assert full_path.exists(), f"Directory {dir_path} missing after second run"
                
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])