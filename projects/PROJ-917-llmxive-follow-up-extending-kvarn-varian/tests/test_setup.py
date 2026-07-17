"""
Tests for the project directory structure setup.

These tests verify that the setup script creates the correct directory 
hierarchy and initializes Python packages properly.
"""
import os
import pytest
from pathlib import Path
import shutil
import tempfile

# Import the setup script functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from setup_directories import DIR_STRUCTURE, create_directories, verify_structure

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate a project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_directory_structure_defined():
    """Test that the directory structure is properly defined."""
    assert len(DIR_STRUCTURE) == 3, "Should have exactly 3 base directories (code, data, tests)"
    
    base_names = [base.name for base, _ in DIR_STRUCTURE]
    assert "code" in base_names
    assert "data" in base_names
    assert "tests" in base_names

def test_code_subdirectories_defined():
    """Test that code subdirectories are properly defined."""
    code_dirs = [d for base, dirs in DIR_STRUCTURE if base.name == "code" for d in dirs]
    expected = ["data_generation", "model_training", "simulation", "analysis"]
    assert set(code_dirs) == set(expected)

def test_data_subdirectories_defined():
    """Test that data subdirectories are properly defined."""
    data_dirs = [d for base, dirs in DIR_STRUCTURE if base.name == "data" for d in dirs]
    expected = ["generated", "models", "simulation", "analysis"]
    assert set(data_dirs) == set(expected)

def test_tests_subdirectories_defined():
    """Test that tests subdirectories are properly defined."""
    test_dirs = [d for base, dirs in DIR_STRUCTURE if base.name == "tests" for d in dirs]
    expected = ["test_data_generation", "test_model_training", "test_simulation"]
    assert set(test_dirs) == set(expected)

def test_create_directories_in_temp(temp_project_root):
    """Test that create_directories creates the correct structure in a temp directory."""
    # Temporarily override PROJECT_ROOT
    original_root = None
    import setup_directories
    original_root = setup_directories.PROJECT_ROOT
    setup_directories.PROJECT_ROOT = temp_project_root
    
    try:
        # Run the creation
        create_directories()
        
        # Verify structure
        for base_path, subdirs in DIR_STRUCTURE:
            # Use the temp project root
            actual_base = temp_project_root / base_path.name
            assert actual_base.exists(), f"Base directory {actual_base} should exist"
            
            for subdir in subdirs:
                actual_subdir = actual_base / subdir
                assert actual_subdir.exists(), f"Subdirectory {actual_subdir} should exist"
                
                # Check for __init__.py in Python package directories
                if base_path.name in ["code", "tests"]:
                    init_file = actual_subdir / "__init__.py"
                    assert init_file.exists(), f"__init__.py should exist in {actual_subdir}"
    finally:
        # Restore original
        if original_root:
            setup_directories.PROJECT_ROOT = original_root

def test_verify_structure_in_temp(temp_project_root):
    """Test that verify_structure works correctly."""
    import setup_directories
    original_root = setup_directories.PROJECT_ROOT
    setup_directories.PROJECT_ROOT = temp_project_root
    
    try:
        # First create the directories
        create_directories()
        
        # Then verify
        result = verify_structure()
        assert result is True, "verify_structure should return True after creation"
    finally:
        if original_root:
            setup_directories.PROJECT_ROOT = original_root
