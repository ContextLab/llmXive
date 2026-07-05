"""
Unit tests for directory setup functionality.

These tests verify that the directory structure creation
functions work correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the setup function
import sys
from pathlib import Path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_directories import create_directories

class TestDirectoryCreation:
    """Test cases for directory creation functionality."""

    def test_create_directories_returns_boolean(self):
        """Test that create_directories returns a boolean."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                result = create_directories()
                assert isinstance(result, bool)
            finally:
                os.chdir(original_cwd)

    def test_create_directories_creates_data_subdirs(self):
        """Test that data/ subdirectories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                create_directories()
                
                # Check data subdirectories
                assert os.path.exists("data/raw")
                assert os.path.exists("data/processed")
                assert os.path.exists("data/output")
            finally:
                os.chdir(original_cwd)

    def test_create_directories_creates_code_subdirs(self):
        """Test that code/ subdirectories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                create_directories()
                
                # Check code subdirectories
                assert os.path.exists("code/utils")
                assert os.path.exists("code/models")
                assert os.path.exists("code/tests")
            finally:
                os.chdir(original_cwd)

    def test_create_directories_creates_tests_subdirs(self):
        """Test that tests/ subdirectories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                create_directories()
                
                # Check tests subdirectories
                assert os.path.exists("tests/unit")
                assert os.path.exists("tests/integration")
            finally:
                os.chdir(original_cwd)

    def test_create_directories_creates_specs_dir(self):
        """Test that specs/ directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                create_directories()
                
                # Check specs directory
                assert os.path.exists("specs")
            finally:
                os.chdir(original_cwd)

    def test_create_directories_idempotent(self):
        """Test that calling create_directories multiple times is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                # Call multiple times
                result1 = create_directories()
                result2 = create_directories()
                
                assert result1 is True
                assert result2 is True
                
                # Verify structure still exists
                assert os.path.exists("data/raw")
                assert os.path.exists("tests/unit")
            finally:
                os.chdir(original_cwd)
