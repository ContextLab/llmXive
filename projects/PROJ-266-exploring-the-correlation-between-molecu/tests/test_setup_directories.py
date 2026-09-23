"""
Tests for the setup_directories module (Task T008a).
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.config import get_project_root
from data.setup_directories import create_directories, verify_directories

def test_create_directories():
    """Test that create_directories creates the required directories."""
    # Get the project root
    project_root = get_project_root()
    
    # Define the expected directories
    expected_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state" / "projects",
        project_root / "state" / "pending",
    ]
    
    # Create the directories
    create_directories()
    
    # Verify that all directories exist
    for directory in expected_dirs:
        assert directory.is_dir(), f"Directory {directory} was not created"

def test_verify_directories():
    """Test that verify_directories passes when directories exist."""
    project_root = get_project_root()
    
    # Create the directories first
    create_directories()
    
    # Verify that the directories exist
    verify_directories(project_root)

def test_verify_directories_fails_when_missing():
    """Test that verify_directories fails when a directory is missing."""
    project_root = get_project_root()
    
    # Temporarily remove a directory to test failure
    test_dir = project_root / "data" / "raw"
    if test_dir.exists():
        # Remove the directory
        test_dir.rmdir()
        
        # Verify that the function raises an AssertionError
        with pytest.raises(AssertionError):
            verify_directories(project_root)
        
        # Recreate the directory for cleanup
        test_dir.mkdir(parents=True, exist_ok=True)
    else:
        # If the directory doesn't exist, verify that the function raises an AssertionError
        with pytest.raises(AssertionError):
            verify_directories(project_root)