"""
Unit tests for the setup_dirs.py script logic.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path for imports if running from tests
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_dirs import main

class TestSetupDirs:
    def test_directory_creation(self, tmp_path):
        """Test that the script creates the required directory structure."""
        # Mock the CWD to be our temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # We need to patch the main function to use tmp_path as root
            # Since main() uses Path.cwd(), we can just run it in the temp dir context
            # but we need to adjust the target path logic or verify the result manually.
            # The script hardcodes "projects/PROJ-191..." relative to CWD.
            
            result = main()
            assert result == 0
            
            project_root = tmp_path / "projects" / "PROJ-191-investigating-the-validity-of-the-invers"
            assert project_root.exists()
            assert project_root.is_dir()
            
            # Check specific required subdirectories
            required_dirs = [
                "code", "tests", "data", "docs",
                "code/data", "code/models", "code/inference", "code/robustness", "code/utils",
                "data/raw", "data/processed", "data/results",
                "tests/unit", "tests/contract", "tests/integration"
            ]
            
            for dir_name in required_dirs:
                dir_path = project_root / dir_name
                assert dir_path.exists(), f"Missing directory: {dir_path}"
                assert dir_path.is_dir(), f"Not a directory: {dir_path}"
                
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path):
        """Test that running the script twice does not cause errors."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run twice
            result1 = main()
            result2 = main()
            
            assert result1 == 0
            assert result2 == 0
            
            project_root = tmp_path / "projects" / "PROJ-191-investigating-the-validity-of-the-invers"
            assert project_root.exists()
            
        finally:
            os.chdir(original_cwd)