import os
import pytest
from pathlib import Path
from setup_project_structure import create_project_structure

def test_project_structure_creation():
    """
    Test that the project structure is created correctly.
    This test verifies that all required directories exist after running create_project_structure.
    """
    # Run the structure creation
    project_root = Path("projects/PROJ-056-the-impact-of-musical-training-on-functi")
    
    # Call the function
    create_project_structure()
    
    # Define expected directories
    expected_dirs = [
        project_root / "code" / "data",
        project_root / "code" / "analysis",
        project_root / "code" / "utils",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "specs" / "001-the-impact-of-musical-training-on-functi",
        project_root / "contracts",
    ]
    
    # Verify all directories exist
    for directory in expected_dirs:
        assert directory.exists(), f"Directory {directory} was not created"
        assert directory.is_dir(), f"{directory} exists but is not a directory"
    
    # Verify the root project directory exists
    assert project_root.exists(), "Project root directory was not created"
    assert project_root.is_dir(), "Project root exists but is not a directory"

def test_directory_tree_integrity():
    """
    Verify the hierarchical integrity of the created directory tree.
    Ensures parent directories exist when child directories are created.
    """
    project_root = Path("projects/PROJ-056-the-impact-of-musical-training-on-functi")
    
    # Check specific deep paths
    deep_paths = [
        project_root / "code" / "data",
        project_root / "tests" / "unit",
        project_root / "specs" / "001-the-impact-of-musical-training-on-functi",
    ]
    
    for path in deep_paths:
        assert path.exists(), f"Deep path {path} does not exist"
        
        # Verify parent exists
        parent = path.parent
        while parent != project_root:
            assert parent.exists(), f"Parent directory {parent} of {path} does not exist"
            parent = parent.parent
    
    # Verify project root is a valid directory
    assert project_root.is_dir(), "Project root is not a directory"