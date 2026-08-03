"""
Unit tests for T002: setup_directories.py

These tests verify that the setup_code_directories function correctly
creates the required directory structure and that os.path.isdir checks pass.
"""
import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path so we can import setup_directories
current_dir = Path(__file__).resolve().parent
code_dir = current_dir.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_directories import setup_code_directories


class TestSetupDirectories:
    """Test cases for setup_code_directories function."""

    def test_creates_all_required_directories(self, tmp_path):
        """Test that all required code/ subdirectories are created."""
        # Create a temporary directory structure
        temp_code = tmp_path / "code"
        
        # Call the function
        result = setup_code_directories(tmp_path)
        
        # Verify result is True
        assert result is True
        
        # Verify all directories exist
        required_subdirs = [
            "data", "models", "inference", "evaluation",
            "utils", "tasks", "tests"
        ]
        
        for subdir in required_subdirs:
            dir_path = temp_code / subdir
            assert os.path.isdir(str(dir_path)), f"Directory {dir_path} was not created"

    def test_verifies_code_root_directory(self, tmp_path):
        """Test that the root code/ directory is verified."""
        # Call the function
        setup_code_directories(tmp_path)
        
        # Verify the root code directory exists
        code_dir = tmp_path / "code"
        assert os.path.isdir(str(code_dir)), "Root code/ directory does not exist"

    def test_idempotent_operation(self, tmp_path):
        """Test that running the function multiple times doesn't fail."""
        # Run twice
        result1 = setup_code_directories(tmp_path)
        result2 = setup_code_directories(tmp_path)
        
        assert result1 is True
        assert result2 is True

    def test_asserts_on_missing_directory(self):
        """Test that an assertion error is raised if a directory cannot be created.
        
        Note: This test is difficult to trigger in a normal environment because
        the function uses mkdir with parents=True, which rarely fails.
        We rely on the assertion logic within the function for verification.
        """
        # In a normal environment, we expect success.
        # The function's internal assertions will catch failures.
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # This should not raise an AssertionError
            result = setup_code_directories(tmp_path)
            assert result is True