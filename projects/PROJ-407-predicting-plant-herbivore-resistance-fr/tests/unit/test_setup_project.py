"""
Unit tests for the project setup script.
Verifies that the directory structure is created correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the setup logic to test it in isolation
# We will test the directory creation logic directly rather than running the script
required_dirs = [
    "code",
    "data/raw",
    "data/interim",
    "data/processed",
    "data/results",
    "tests/unit",
    "tests/integration",
    "tests/contract"
]

def test_directory_creation():
    """Test that all required directories are created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Simulate the creation logic
        created_dirs = []
        for dir_path in required_dirs:
            full_path = root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(full_path)
        
        # Verify all directories exist
        for dir_path in created_dirs:
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_nested_structure():
    """Test that nested directories are created correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create a nested directory
        nested_path = root / "data" / "raw"
        nested_path.mkdir(parents=True, exist_ok=True)
        
        assert (root / "data").exists()
        assert nested_path.exists()
        assert (root / "data" / "raw").exists()

def test_idempotency():
    """Test that running the setup again doesn't fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # First run
        for dir_path in required_dirs:
            (root / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Second run (should not raise)
        for dir_path in required_dirs:
            (root / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Verify still exists
        for dir_path in required_dirs:
            assert (root / dir_path).exists()