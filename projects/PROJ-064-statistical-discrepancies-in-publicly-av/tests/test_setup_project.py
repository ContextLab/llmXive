"""
Tests for the project setup script.
Verifies that the directory structure is created correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project import initialize_project_structure

def test_initialize_project_structure():
    """Test that the project directory structure is created correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_name = "PROJ-064-statistical-discrepancies-in-publicly-av"
        project_root = Path(tmp_dir) / project_name
        
        initialize_project_structure(tmp_dir)
        
        # Verify the project root exists
        assert project_root.exists(), "Project root directory was not created"
        assert project_root.is_dir(), "Project root is not a directory"
        
        # Verify all subdirectories exist
        expected_dirs = [
            "code",
            "data",
            "data/raw",
            "data/processed",
            "tests",
            "docs",
            "state",
            "config",
        ]
        
        for dir_path in expected_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"

def test_idempotency():
    """Test that running the script multiple times does not cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Run twice
        initialize_project_structure(tmp_dir)
        initialize_project_structure(tmp_dir)
        
        # Verify structure still exists
        project_name = "PROJ-064-statistical-discrepancies-in-publicly-av"
        project_root = Path(tmp_dir) / project_name
        
        assert project_root.exists()
        assert (project_root / "code").exists()
        assert (project_root / "data" / "raw").exists()