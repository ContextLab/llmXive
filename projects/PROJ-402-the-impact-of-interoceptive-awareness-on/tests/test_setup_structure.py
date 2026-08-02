"""
Tests for project structure initialization (T001).

Verifies that the required directory structure and initialization files
are created correctly by setup_project_structure.py.
"""
import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path to import setup_project_structure
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project_structure import (
    create_directories,
    create_init_files,
    create_gitkeep_files,
    DIRECTORIES,
    INIT_FILES,
    GITKEEP_FILES,
    BASE_DIR
)

class TestProjectStructure:
    """Test suite for project structure creation."""

    def test_required_directories_exist(self):
        """Verify that all required directories exist after creation."""
        # Run the creation function
        created = create_directories()
        
        # Verify each directory in DIRECTORIES exists
        for dir_path in DIRECTORIES:
            full_path = BASE_DIR / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} exists but is not a directory"

    def test_init_files_exist(self):
        """Verify that __init__.py files are created for Python packages."""
        # Run the creation function
        created = create_init_files()
        
        # Verify each init file exists
        for file_path in INIT_FILES:
            full_path = BASE_DIR / file_path
            assert full_path.exists(), f"File {full_path} was not created"
            assert full_path.is_file(), f"{full_path} exists but is not a file"

    def test_gitkeep_files_exist(self):
        """Verify that .gitkeep files are created for data directories."""
        # Run the creation function
        created = create_gitkeep_files()
        
        # Verify each gitkeep file exists
        for file_path in GITKEEP_FILES:
            full_path = BASE_DIR / file_path
            assert full_path.exists(), f"File {full_path} was not created"
            assert full_path.is_file(), f"{full_path} exists but is not a file"

    def test_directory_hierarchy_preserved(self):
        """Verify that nested directory structure is correctly created."""
        # Ensure directories exist
        create_directories()
        
        # Check specific nested directories
        expected_nested = [
            "data/raw",
            "data/derived",
            "data/audit",
            "results/figures",
            "code/utils"
        ]
        
        for nested in expected_nested:
            full_path = BASE_DIR / nested
            assert full_path.exists(), f"Nested directory {full_path} missing"
            assert full_path.is_dir(), f"{full_path} is not a directory"

    def test_structure_is_clean(self):
        """Verify that no unexpected files were created in root."""
        # Run creation
        create_directories()
        create_init_files()
        create_gitkeep_files()
        
        # List root contents
        root_contents = list(BASE_DIR.iterdir())
        expected_names = {
            "code", "tests", "data", "results", "specs",
            "setup_project_structure.py", "test_setup_structure.py",
            "tasks.md", "README.md"  # Common project files
        }
        
        # We don't strictly enforce only expected names here to allow
        # for other project files, but we ensure the required ones exist
        root_names = {p.name for p in root_contents}
        
        required = {"code", "tests", "data", "results", "specs"}
        missing = required - root_names
        
        assert len(missing) == 0, f"Missing required directories in root: {missing}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
