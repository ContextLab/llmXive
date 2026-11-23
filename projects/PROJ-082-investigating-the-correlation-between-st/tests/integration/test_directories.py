import os
import pytest
from pathlib import Path
from code.setup_directories import create_directories, verify_structure

def test_directory_creation():
    """Test that the setup script creates the required directories."""
    # Run the creation logic
    created = create_directories()
    
    # Verify structure
    is_valid, missing = verify_structure()
    
    assert is_valid, f"Missing directories after creation: {missing}"
    
    # Check root directories exist
    project_root = Path.cwd()
    assert (project_root / "code").is_dir()
    assert (project_root / "tests").is_dir()
    assert (project_root / "data").is_dir()
    assert (project_root / "docs").is_dir()

def test_data_subdirectories():
    """Test that data subdirectories are created."""
    project_root = Path.cwd()
    required_data_dirs = ["raw", "derived", "interim"]
    
    for subdir in required_data_dirs:
        assert (project_root / "data" / subdir).is_dir(), f"Missing data/{subdir}"

def test_test_subdirectories():
    """Test that test subdirectories are created."""
    project_root = Path.cwd()
    required_test_dirs = ["unit", "integration", "contract"]
    
    for subdir in required_test_dirs:
        assert (project_root / "tests" / subdir).is_dir(), f"Missing tests/{subdir}"