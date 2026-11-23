"""
Tests for the project setup module.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import setup_project
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from setup_project import create_project_structure


def test_create_project_structure():
    """Test that create_project_structure creates all required directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create the structure in a temporary directory
        create_project_structure(tmp_dir)
        
        root_path = Path(tmp_dir)
        
        # Define required directories
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "tests",
            "docs",
            "state/projects",
        ]
        
        # Verify each directory exists
        for dir_path in required_dirs:
            full_path = root_path / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"Path {full_path} is not a directory"
        
        # Verify nested structure exists (e.g., data/raw exists as a directory)
        assert (root_path / "data" / "raw").exists()
        assert (root_path / "data" / "processed").exists()
        assert (root_path / "state" / "projects").exists()


def test_create_project_structure_idempotent():
    """Test that running create_project_structure twice doesn't fail."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create structure first time
        create_project_structure(tmp_dir)
        
        # Create structure second time (should not raise)
        create_project_structure(tmp_dir)
        
        # Verify structure still exists
        root_path = Path(tmp_dir)
        assert (root_path / "code").exists()
        assert (root_path / "data" / "raw").exists()