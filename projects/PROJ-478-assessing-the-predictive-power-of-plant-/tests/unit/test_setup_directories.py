import os
import tempfile
import shutil
import sys
import pytest

# Add the code directory to the path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from setup_directories import create_directories

class TestCreateDirectories:
    def test_creates_all_required_directories(self, tmp_path):
        """Test that all required directories are created."""
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the function
            result = create_directories()
            
            # Check that all keys exist in result
            expected_dirs = ["data/raw", "data/processed", "data/metadata", "results"]
            for dir_name in expected_dirs:
                assert dir_name in result, f"Missing directory {dir_name} in result"
                
                # Check that the directory actually exists on disk
                full_path = result[dir_name]
                assert os.path.exists(full_path), f"Directory {full_path} was not created"
                assert os.path.isdir(full_path), f"{full_path} is not a directory"
                
        finally:
            os.chdir(original_cwd)

    def test_directories_are_nested_correctly(self, tmp_path):
        """Test that data subdirectories are nested under data/."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = create_directories()
            
            # Verify nesting
            assert result["data/raw"].endswith("data/raw")
            assert result["data/processed"].endswith("data/processed")
            assert result["data/metadata"].endswith("data/metadata")
            assert result["results"].endswith("results")
            
            # Verify parent directory exists
            assert os.path.exists(os.path.join(tmp_path, "data"))
            
        finally:
            os.chdir(original_cwd)

    def test_no_error_if_directories_exist(self, tmp_path):
        """Test that the function handles existing directories gracefully."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Pre-create one directory
            os.makedirs("data/raw")
            
            # Should not raise an exception
            result = create_directories()
            
            assert "data/raw" in result
            
        finally:
            os.chdir(original_cwd)

    def test_returns_absolute_paths(self, tmp_path):
        """Test that the returned paths are absolute."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = create_directories()
            
            for path in result.values():
                assert os.path.isabs(path), f"Path {path} is not absolute"
                
        finally:
            os.chdir(original_cwd)