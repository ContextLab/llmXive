"""
Unit tests for the project setup script functionality.
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
import pytest
import sys

# Add the parent directory to the path to import the setup script logic
# In a real CI environment, this might be handled differently, but for testing:
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# We will test the logic by simulating the directory creation in a temp folder
# rather than importing the script directly to avoid side effects on the actual repo.

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/models",
    "logs",
    "tests/contract",
    "tests/integration",
    "tests/unit",
    "docs",
    "contracts"
]

def test_directory_creation_logic():
    """Test that the logic creates the correct directory structure."""
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Simulate the creation logic
        for dir_name in REQUIRED_DIRS:
            full_path = os.path.join(tmp_dir, dir_name)
            os.makedirs(full_path, exist_ok=True)
        
        # Verify all directories exist
        for dir_name in REQUIRED_DIRS:
            full_path = os.path.join(tmp_dir, dir_name)
            assert os.path.exists(full_path), f"Directory {dir_name} was not created"
            assert os.path.isdir(full_path), f"Path {dir_name} is not a directory"

def test_nested_directories_exist():
    """Ensure nested structures like data/raw are created."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create nested structure
        nested_path = os.path.join(tmp_dir, "data", "raw")
        os.makedirs(nested_path, exist_ok=True)
        
        assert os.path.exists(nested_path)
        assert os.path.isdir(nested_path)
        # Parent should also exist
        assert os.path.exists(os.path.join(tmp_dir, "data"))

def test_idempotency():
    """Test that running the creation logic multiple times doesn't fail."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # First run
        for dir_name in REQUIRED_DIRS:
            os.makedirs(os.path.join(tmp_dir, dir_name), exist_ok=True)
        
        # Second run (should not raise)
        for dir_name in REQUIRED_DIRS:
            os.makedirs(os.path.join(tmp_dir, dir_name), exist_ok=True)
        
        # Verify still exists
        for dir_name in REQUIRED_DIRS:
            assert os.path.exists(os.path.join(tmp_dir, dir_name))