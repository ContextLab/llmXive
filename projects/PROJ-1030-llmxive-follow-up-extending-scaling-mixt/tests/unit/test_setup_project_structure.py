"""
Unit tests for the project structure setup script (T001).

These tests verify that the directory creation logic works correctly
and handles edge cases appropriately.
"""

import os
import tempfile
import shutil
import pytest

# Import the function to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from code.setup_project_structure import create_directories


class TestCreateDirectories:
    """Tests for the create_directories function."""

    def test_creates_all_required_directories(self):
        """Test that all required directories are created."""
        # Create a temporary directory to act as project root
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_dir = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Run the function
                result = create_directories()
                
                # Verify success
                assert result is True
                
                # Verify all directories exist
                required_dirs = [
                    "code",
                    "code/utils",
                    "data/raw",
                    "data/processed",
                    "tests/unit",
                    "tests/integration",
                    "docs/figures",
                    "state",
                ]
                
                for dir_path in required_dirs:
                    full_path = os.path.join(temp_dir, dir_path)
                    assert os.path.isdir(full_path), f"Directory {dir_path} was not created"

            finally:
                os.chdir(original_dir)

    def test_idempotent_operation(self):
        """Test that running the function multiple times doesn't cause errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_dir = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Run twice
                result1 = create_directories()
                result2 = create_directories()
                
                assert result1 is True
                assert result2 is True
                
            finally:
                os.chdir(original_dir)

    def test_creates_nested_directories(self):
        """Test that nested directories are created correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_dir = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                result = create_directories()
                assert result is True
                
                # Verify nested structure
                assert os.path.isdir("code/utils")
                assert os.path.isdir("data/raw")
                assert os.path.isdir("data/processed")
                assert os.path.isdir("tests/unit")
                assert os.path.isdir("tests/integration")
                assert os.path.isdir("docs/figures")
                
            finally:
                os.chdir(original_dir)

    def test_handles_existing_directories(self):
        """Test that existing directories don't cause errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_dir = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Pre-create some directories
                os.makedirs("code", exist_ok=True)
                os.makedirs("data", exist_ok=True)
                
                # Run the function
                result = create_directories()
                
                # Should still succeed
                assert result is True
                assert os.path.isdir("code/utils")
                assert os.path.isdir("data/raw")
                
            finally:
                os.chdir(original_dir)

    def test_return_value_on_success(self):
        """Test that the function returns True on success."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_dir = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = create_directories()
                assert result is True
            finally:
                os.chdir(original_dir)