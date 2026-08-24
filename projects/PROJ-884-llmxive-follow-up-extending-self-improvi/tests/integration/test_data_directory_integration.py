"""
Integration tests for data directory setup.
Verifies end-to-end functionality of directory creation and usage.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import setup_data_directories

class TestDataDirectoryIntegration:
    """Integration tests for data directory setup."""

    def test_full_workflow(self, tmp_path):
        """Test the complete workflow of directory setup and usage."""
        # Setup directories
        directories = setup_data_directories(tmp_path)
        
        # Get specific directories
        data_dir = directories[0]
        raw_dir = directories[1]
        processed_dir = directories[2]
        
        # Test writing to raw directory
        test_puzzle = {
            "id": "test_001",
            "type": "sudoku",
            "constraints": ["row", "column", "box"],
            "data": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        }
        
        puzzle_file = raw_dir / "puzzle_001.json"
        with open(puzzle_file, 'w') as f:
            json.dump(test_puzzle, f)
        
        assert puzzle_file.exists()
        
        # Test writing to processed directory
        test_log = {
            "experiment_id": "exp_001",
            "timestamp": "2024-01-01T00:00:00",
            "status": "completed"
        }
        
        log_file = processed_dir / "experiment_log.json"
        with open(log_file, 'w') as f:
            json.dump(test_log, f)
        
        assert log_file.exists()
        
        # Verify we can read the files back
        with open(puzzle_file, 'r') as f:
            loaded_puzzle = json.load(f)
        assert loaded_puzzle["id"] == "test_001"
        
        with open(log_file, 'r') as f:
            loaded_log = json.load(f)
        assert loaded_log["status"] == "completed"

    def test_directory_permissions_workflow(self, tmp_path):
        """Test that directories maintain correct permissions throughout workflow."""
        directories = setup_data_directories(tmp_path)
        
        # Verify initial permissions
        for dir_path in directories:
            assert os.access(dir_path, os.R_OK), f"{dir_path} should be readable"
            assert os.access(dir_path, os.W_OK), f"{dir_path} should be writable"
            assert os.access(dir_path, os.X_OK), f"{dir_path} should be executable"
        
        # Create some files
        raw_dir = directories[1]
        test_file = raw_dir / "test.txt"
        test_file.write_text("test")
        
        # Verify permissions still hold after file creation
        for dir_path in directories:
            assert os.access(dir_path, os.R_OK)
            assert os.access(dir_path, os.W_OK)
            assert os.access(dir_path, os.X_OK)

    def test_nested_directory_creation(self, tmp_path):
        """Test that deeply nested directories are created correctly."""
        # Remove existing data directory if it exists
        data_dir = tmp_path / "data"
        if data_dir.exists():
            import shutil
            shutil.rmtree(data_dir)
        
        # Setup should create the full hierarchy
        directories = setup_data_directories(tmp_path)
        
        # Verify the full path exists
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        
        # Test creating nested subdirectories within processed
        nested_dir = directories[2] / "subdir" / "nested"
        nested_dir.mkdir(parents=True, exist_ok=True)
        assert nested_dir.exists()
        
        # Write a file in the nested directory
        nested_file = nested_dir / "deep_file.json"
        with open(nested_file, 'w') as f:
            json.dump({"test": "data"}, f)
        
        assert nested_file.exists()
        with open(nested_file, 'r') as f:
            assert json.load(f)["test"] == "data"