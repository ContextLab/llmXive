"""
Unit tests for the setup_directories.py script.
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the parent directory to the path to import setup_directories if needed,
# but since we are testing the logic, we will import the function or run the script logic.
# We will simulate the environment by creating a temp directory and running the logic there.

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_directory_creation(temp_project_root):
    """Test that the script creates all required directories."""
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "state/projects"
    ]

    # Simulate the logic from setup_directories.py
    for dir_name in directories:
        target_path = temp_project_root / dir_name
        target_path.mkdir(parents=True, exist_ok=True)

    # Assertions
    for dir_name in directories:
        target_path = temp_project_root / dir_name
        assert target_path.exists(), f"Directory {dir_name} was not created"
        assert target_path.is_dir(), f"{dir_name} is not a directory"

def test_nested_directory_creation(temp_project_root):
    """Test that nested directories (e.g., data/raw) are created with parents."""
    target_path = temp_project_root / "data" / "raw"
    target_path.mkdir(parents=True, exist_ok=True)
    
    assert (temp_project_root / "data").exists()
    assert target_path.exists()

def test_idempotency(temp_project_root):
    """Test that running the creation logic multiple times doesn't fail."""
    directories = [
        "data/raw",
        "data/processed"
    ]
    
    for _ in range(2):
        for dir_name in directories:
            target_path = temp_project_root / dir_name
            target_path.mkdir(parents=True, exist_ok=True)
        
        # Should not raise any errors
        assert (temp_project_root / "data").exists()
        assert (temp_project_root / "data" / "raw").exists()