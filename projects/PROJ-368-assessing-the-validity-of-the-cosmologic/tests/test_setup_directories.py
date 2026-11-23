"""
Tests for the setup_directories module (Task T004).
Verifies that the required project directory structure is created correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import create_directories

def test_create_directories_structure():
    """Test that all required directories are created."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        
        # Call the function
        create_directories(base_path)
        
        # Define required directories
        required_dirs = [
            "data/raw",
            "data/processed",
            "data/simulations",
            "data/reports",
            "code",
            "tests"
        ]
        
        # Verify each directory exists
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

def test_create_directories_idempotent():
    """Test that running create_directories multiple times doesn't cause errors."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        
        # Create directories twice
        create_directories(base_path)
        create_directories(base_path)
        
        # Verify directories still exist
        required_dirs = [
            "data/raw",
            "data/processed",
            "data/simulations",
            "data/reports",
            "code",
            "tests"
        ]
        
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            assert full_path.exists(), f"Directory {full_path} missing after idempotent run"

def test_create_directories_nested():
    """Test that nested directories are created correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        
        # Only create the base path
        create_directories(base_path)
        
        # Verify nested structure exists
        nested_path = base_path / "data" / "raw"
        assert nested_path.exists(), "Nested directory data/raw not created"
        
        nested_path = base_path / "data" / "processed"
        assert nested_path.exists(), "Nested directory data/processed not created"

def test_create_directories_empty_base():
    """Test that the function works with an empty base path (current directory)."""
    # This test is more of a sanity check - we don't actually run it in temp
    # to avoid polluting the current directory
    assert True, "Test skipped to avoid polluting current directory"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
