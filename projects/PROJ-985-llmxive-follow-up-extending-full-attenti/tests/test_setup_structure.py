import os
import pytest
from setup_project_structure import create_directories, verify_structure

def test_directory_creation(tmp_path):
    """Test that create_directories creates the required structure."""
    # Save original cwd
    original_cwd = os.getcwd()
    try:
        # Change to temp directory
        os.chdir(tmp_path)
        
        # Run creation
        created = create_directories()
        
        # Verify all required directories exist
        required = [
            "code",
            "tests",
            "data",
            os.path.join("code", "lib"),
            os.path.join("code", "data"),
            os.path.join("code", "models"),
            os.path.join("code", "evaluation"),
            os.path.join("data", "results"),
            os.path.join("data", "logs"),
            os.path.join("data", "intermediate"),
        ]
        
        for dir_path in required:
            full_path = os.path.join(tmp_path, dir_path)
            assert os.path.isdir(full_path), f"Directory {dir_path} was not created"
    finally:
        # Restore original cwd
        os.chdir(original_cwd)

def test_verify_structure_success(tmp_path):
    """Test that verify_structure returns True when all dirs exist."""
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        create_directories()
        assert verify_structure() is True
    finally:
        os.chdir(original_cwd)