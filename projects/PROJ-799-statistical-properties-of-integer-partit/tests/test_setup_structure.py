"""
Test suite for project structure initialization.

This test verifies that the setup_structure.py script correctly creates
all required directories for the PROJ-799 project.
"""
import os
import pytest
from pathlib import Path
import shutil
import tempfile

# Import the module to test
import code.setup_structure as setup_module


class TestProjectStructure:
    """Test cases for project structure creation."""
    
    @pytest.fixture
    def temp_project_dir(self, tmp_path):
        """Create a temporary project directory for testing."""
        # Save original cwd
        original_cwd = os.getcwd()
        
        # Create a temporary directory to act as project root
        temp_root = tmp_path / "projects" / "PROJ-799-statistical-properties-of-integer-partit"
        temp_root.mkdir(parents=True, exist_ok=True)
        
        # Change to temp directory to simulate project root
        os.chdir(temp_root.parent)
        
        yield temp_root
        
        # Restore original cwd
        os.chdir(original_cwd)
    
    def test_required_directories_exist(self, temp_project_dir):
        """Verify all required directories are created by the setup script."""
        # Define expected directories relative to project root
        expected_dirs = [
            "code",
            "code/utils",
            "data/raw",
            "data/processed",
            "data/schemas",
            "tests",
            "tests/data",
            "docs",
            "state/projects",
        ]
        
        # Check each expected directory exists
        for dir_path in expected_dirs:
            full_path = temp_project_dir / dir_path
            assert full_path.exists(), f"Directory {dir_path} does not exist"
            assert full_path.is_dir(), f"{dir_path} is not a directory"
    
    def test_setup_structure_creates_all_directories(self, temp_project_dir):
        """Test that the setup script creates all required directories."""
        # Run the setup function
        result = setup_module.main()
        
        # Verify return code is 0 (success)
        assert result == 0, f"Setup script returned non-zero exit code: {result}"
        
        # Verify all expected directories exist
        expected_dirs = [
            "code",
            "code/utils",
            "data/raw",
            "data/processed",
            "data/schemas",
            "tests",
            "tests/data",
            "docs",
            "state/projects",
        ]
        
        for dir_path in expected_dirs:
            full_path = temp_project_dir / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"