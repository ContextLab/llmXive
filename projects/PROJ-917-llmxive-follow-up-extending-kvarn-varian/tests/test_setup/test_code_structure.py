"""
Tests for the code directory structure setup.

This module verifies that the setup_code_structure.py script correctly
creates the required directory structure under the 'code/' directory.
"""
import pytest
import os
from pathlib import Path
import tempfile
import shutil
import sys

# Add the code directory to the path for imports
@pytest.fixture(autouse=True)
def setup_path():
    """Ensure code directory is in the path for imports."""
    code_path = Path(__file__).parent.parent.parent / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))

class TestCodeStructureSetup:
    """Tests for the code directory structure setup functionality."""

    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Create a temporary project root for testing."""
        # Create a temporary directory to act as project root
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # Create a code directory within it
        code_dir = project_root / "code"
        code_dir.mkdir()
        
        return project_root

    def test_directory_creation(self, temp_project_root):
        """Test that all required subdirectories are created."""
        from setup_code_structure import create_directories, verify_structure
        
        # Run the creation function
        create_directories(temp_project_root)
        
        # Verify the structure
        assert verify_structure(temp_project_root), "Directory structure verification failed"
        
        # Check each required directory exists
        required_dirs = [
            "data_generation",
            "model_training",
            "simulation",
            "analysis"
        ]
        
        for subdir in required_dirs:
            dir_path = temp_project_root / "code" / subdir
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_init_files_created(self, temp_project_root):
        """Test that __init__.py files are created for Python packages."""
        from setup_code_structure import create_directories
        
        # Run the creation function
        create_directories(temp_project_root)
        
        # Check that __init__.py files exist
        required_dirs = [
            "data_generation",
            "model_training",
            "simulation",
            "analysis"
        ]
        
        for subdir in required_dirs:
            init_file = temp_project_root / "code" / subdir / "__init__.py"
            assert init_file.exists(), f"__init__.py not created for {subdir}"
            assert init_file.is_file(), f"{init_file} exists but is not a file"

    def test_idempotency(self, temp_project_root):
        """Test that running the setup multiple times doesn't cause errors."""
        from setup_code_structure import create_directories, verify_structure
        
        # Run twice
        create_directories(temp_project_root)
        create_directories(temp_project_root)
        
        # Should still verify correctly
        assert verify_structure(temp_project_root), "Structure verification failed after multiple runs"

    def test_nested_directory_creation(self, temp_project_root):
        """Test that parent directories are created if they don't exist."""
        from setup_code_structure import create_directories, verify_structure
        
        # Remove the code directory entirely
        code_dir = temp_project_root / "code"
        shutil.rmtree(code_dir, ignore_errors=True)
        
        # Run creation
        create_directories(temp_project_root)
        
        # Verify
        assert verify_structure(temp_project_root), "Structure verification failed after recreating code dir"
        assert (temp_project_root / "code").exists(), "Code directory not recreated"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
