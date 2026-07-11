"""
Tests for T001b: Verify that `data/raw` directory is created.
"""
import os
import pytest
from pathlib import Path

# Import the function to test
try:
    from setup_raw_data_dir import create_directory, main
except ImportError:
    # Fallback if running from different context, though task implies code/
    from code.setup_raw_data_dir import create_directory, main


def test_create_directory_creates_if_missing(tmp_path):
    """Test that create_directory actually creates a new directory."""
    test_dir = tmp_path / "new_dir"
    assert not test_dir.exists()
    
    result = create_directory(str(test_dir))
    
    assert result.exists()
    assert result.is_dir()

def test_create_directory_existent_if_exists(tmp_path):
    """Test that create_directory works if directory already exists."""
    test_dir = tmp_path / "existing_dir"
    test_dir.mkdir()
    assert test_dir.exists()
    
    result = create_directory(str(test_dir))
    
    assert result.exists()
    assert result.is_dir()

def test_data_raw_directory_exists_in_project_root():
    """
    Integration check: Verify that the script creates data/raw 
    relative to the project root (where tests/ and code/ reside).
    """
    # Determine project root (parent of tests/ or code/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent
    
    target_path = project_root / "data" / "raw"
    
    # We expect the directory to exist if the script has been run.
    # If it doesn't exist yet, this test documents the requirement.
    # In a CI/CD flow, this test would run after the script.
    assert target_path.exists(), f"Directory {target_path} must exist. Run code/setup_raw_data_dir.py first."
    assert target_path.is_dir()