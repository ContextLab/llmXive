"""
Tests for data directory setup functionality.
"""
import os
import tempfile
import shutil
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.utils.setup_data import setup_directories


def test_setup_directories_creates_all_needed_dirs():
    """Test that setup_directories creates all required directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp directory to avoid polluting real project structure
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            created = setup_directories()
            
            # Check all expected directories were created
            expected_dirs = ["data", "data/raw", "data/processed", "contracts"]
            for expected in expected_dirs:
                assert os.path.exists(expected), f"Directory {expected} was not created"
                assert os.path.isdir(expected), f"{expected} is not a directory"
            
            # Verify all expected dirs are in created list
            for expected in expected_dirs:
                assert expected in created, f"{expected} not in created list"
        finally:
            os.chdir(original_cwd)


def test_setup_directories_idempotent():
    """Test that running setup_directories twice doesn't fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Run twice
            setup_directories()
            second_run = setup_directories()
            
            # Second run should report existing dirs, not create new ones
            assert len(second_run) == 0, "Second run should not create any directories"
        finally:
            os.chdir(original_cwd)


def test_setup_directories_creates_nested_structure():
    """Test that nested directories are created correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            setup_directories()
            
            # Check nested structure
            assert os.path.exists("data/raw")
            assert os.path.exists("data/processed")
            assert os.path.isdir("data/raw")
            assert os.path.isdir("data/processed")
        finally:
            os.chdir(original_cwd)
