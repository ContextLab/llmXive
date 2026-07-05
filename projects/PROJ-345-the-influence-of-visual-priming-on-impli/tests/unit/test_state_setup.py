"""
Unit tests for state directory creation (T002b).
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_state import create_state_directories

def test_create_state_directories_structure():
    """Test that the state directory structure is created correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create the directories
        create_state_directories(project_root)
        
        # Verify the expected paths exist
        expected_paths = [
            project_root / "state",
            project_root / "state" / "projects",
            project_root / "state" / "projects" / "PROJ-345",
            project_root / "state" / "projects" / "PROJ-345" / "logs",
            project_root / "state" / "projects" / "PROJ-345" / "artifacts",
            project_root / "state" / "projects" / "PROJ-345" / "models",
        ]
        
        for path in expected_paths:
            assert path.exists(), f"Expected path {path} does not exist"
            assert path.is_dir(), f"Expected path {path} is not a directory"
        
        # Verify __init__.py files were created
        init_files = [
            project_root / "state" / "__init__.py",
            project_root / "state" / "projects" / "__init__.py",
            project_root / "state" / "projects" / "PROJ-345" / "__init__.py",
            project_root / "state" / "projects" / "PROJ-345" / "logs" / "__init__.py",
            project_root / "state" / "projects" / "PROJ-345" / "artifacts" / "__init__.py",
            project_root / "state" / "projects" / "PROJ-345" / "models" / "__init__.py",
        ]
        
        for init_file in init_files:
            assert init_file.exists(), f"Expected __init__.py at {init_file} does not exist"

def test_create_state_directories_idempotent():
    """Test that running the function twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Run twice
        create_state_directories(project_root)
        create_state_directories(project_root)
        
        # Should still exist
        assert (project_root / "state" / "projects" / "PROJ-345").exists()