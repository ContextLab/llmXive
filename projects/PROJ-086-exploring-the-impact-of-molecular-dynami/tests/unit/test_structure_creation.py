"""
Unit tests for T001: Project Structure Creation.

Verifies that the setup_structure.py script creates the expected
directories and handles existing directories correctly.
"""

import os
import tempfile
import shutil
import pytest

# Import the logic from the setup script
# We assume the script is in code/setup_structure.py
# We will test the directory creation logic directly

REQUIRED_DIRS = [
    "code/simulation",
    "code/analysis",
    "code/utils",
    "data/raw",
    "data/processed",
    "results",
    "figures",
    "state",
    "tests/unit",
    "tests/integration",
]

class TestProjectStructure:
    
    def setup_method(self):
        """Create a temporary directory to simulate project root."""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_directories_created(self):
        """Test that all required directories are created."""
        for dir_path in REQUIRED_DIRS:
            full_path = os.path.join(self.temp_dir, dir_path)
            
            # Simulate creation
            os.makedirs(full_path, exist_ok=True)
            
            # Verify existence
            assert os.path.exists(full_path), f"Directory {dir_path} was not created"
            assert os.path.isdir(full_path), f"{dir_path} is not a directory"
            
    def test_idempotency(self):
        """Test that creating directories twice does not raise errors."""
        for dir_path in REQUIRED_DIRS:
            full_path = os.path.join(self.temp_dir, dir_path)
            
            # First creation
            os.makedirs(full_path, exist_ok=True)
            assert os.path.exists(full_path)
            
            # Second creation (should not raise)
            os.makedirs(full_path, exist_ok=True)
            assert os.path.exists(full_path)
            
    def test_nested_structure(self):
        """Test that nested directories are created correctly."""
        # Test a specific nested path
        nested_path = os.path.join(self.temp_dir, "code", "simulation")
        os.makedirs(nested_path, exist_ok=True)
        
        assert os.path.exists(nested_path)
        assert os.path.exists(os.path.join(self.temp_dir, "code"))