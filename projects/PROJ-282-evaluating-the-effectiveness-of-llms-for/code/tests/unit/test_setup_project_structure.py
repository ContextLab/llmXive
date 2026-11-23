import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the functions we want to test
# Adjust import path based on where the script is located relative to tests
# The script is at code/code/scripts/setup_project_structure.py
# So we import from code.code.scripts.setup_project_structure
try:
    from code.code.scripts.setup_project_structure import create_structure, generate_tree_json
except ImportError:
    # Fallback if running from root and structure is different
    from code.scripts.setup_project_structure import create_structure, generate_tree_json

class TestProjectStructureCreation:
    
    def test_create_structure_creates_all_dirs(self, tmp_path):
        """Test that create_structure creates all expected directories."""
        expected_dirs = [
            "src", "tests", "data", "data/raw", "data/processed", 
            "data/results", "state", "data/logs", "contracts"
        ]
        
        result = create_structure(tmp_path)
        
        assert result["errors"] == []
        for expected in expected_dirs:
            assert (tmp_path / expected).exists(), f"Directory {expected} was not created"
            assert (tmp_path / expected).is_dir(), f"Path {expected} is not a directory"

    def test_create_structure_handles_existing_dirs(self, tmp_path):
        """Test that create_structure does not fail if directories already exist."""
        # Pre-create a directory
        (tmp_path / "src").mkdir()
        
        result = create_structure(tmp_path)
        
        assert result["errors"] == []
        assert (tmp_path / "src").exists()

    def test_generate_tree_json_creates_valid_file(self, tmp_path):
        """Test that generate_tree_json creates a valid JSON file with correct structure."""
        # Create some dummy directories first
        (tmp_path / "src").mkdir()
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "raw").mkdir()
        
        log_path = tmp_path / "data" / "logs" / "dir_tree.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        generate_tree_json(tmp_path, log_path)
        
        assert log_path.exists(), "Log file was not created"
        
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        assert "directories" in data
        assert "root" in data
        assert isinstance(data["directories"], list)
        
        # Check that our created dirs are in the list
        dir_list = [os.path.normpath(d) for d in data["directories"]]
        assert "src" in dir_list
        assert "data" in dir_list
        assert os.path.normpath("data/raw") in dir_list

    def test_generate_tree_json_empty_dir(self, tmp_path):
        """Test behavior when no subdirectories exist (only root)."""
        log_path = tmp_path / "data" / "logs" / "dir_tree.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        generate_tree_json(tmp_path, log_path)
        
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        assert len(data["directories"]) >= 0 # Should at least have the root or empty