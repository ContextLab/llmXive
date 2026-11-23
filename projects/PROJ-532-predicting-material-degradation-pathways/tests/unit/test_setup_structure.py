"""
Unit tests for the project structure setup module.
Verifies that the required directory hierarchy is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the module under test
# We need to simulate the project root environment
import sys

def test_ensure_dir_creates_directory():
    """Test that ensure_dir creates a directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "new_dir"
        # Import locally to avoid path issues in test runner
        from code.setup_project_structure import ensure_dir
        ensure_dir(test_path)
        assert test_path.exists()
        assert test_path.is_dir()

def test_ensure_dir_no_op_if_exists():
    """Test that ensure_dir does nothing if directory already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "existing_dir"
        test_path.mkdir()
        from code.setup_project_structure import ensure_dir
        ensure_dir(test_path)
        assert test_path.exists()

def test_create_placeholder_file_creates_file():
    """Test that create_placeholder_file creates a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "test_file.txt"
        from code.setup_project_structure import create_placeholder_file
        create_placeholder_file(test_path, "Hello World")
        assert test_path.exists()
        assert test_path.read_text() == "Hello World"

def test_create_placeholder_file_creates_parent_dirs():
    """Test that create_placeholder_file creates parent directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "sub" / "deep" / "test.txt"
        from code.setup_project_structure import create_placeholder_file
        create_placeholder_file(test_path, "Content")
        assert test_path.exists()
        assert test_path.parent.exists()

def test_main_creates_project_structure(tmp_path):
    """
    Test that main() creates the expected directory structure.
    We run it in a temporary directory to avoid polluting the real workspace.
    """
    # Change to temp directory to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Import and run main
        from code.setup_project_structure import main
        main()
        
        # Verify expected directories exist
        project_root = tmp_path / "projects" / "PROJ-532-predicting-material-degradation-pathways"
        
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/contracts",
            "tests/unit",
            "tests/integration",
            "results/metrics",
            "results/plots",
            "results/artifacts",
            "specs",
            "figures",
        ]
        
        for d in expected_dirs:
            dir_path = project_root / d
            assert dir_path.exists(), f"Missing directory: {dir_path}"
            assert dir_path.is_dir(), f"Not a directory: {dir_path}"
        
        # Verify README files exist
        assert (project_root / "README.md").exists()
        assert (project_root / "data" / "README.md").exists()
        assert (project_root / "results" / "README.md").exists()
        
        # Verify __init__.py files exist
        assert (project_root / "code" / "__init__.py").exists()
        assert (project_root / "tests" / "__init__.py").exists()
        assert (project_root / "tests" / "unit" / "__init__.py").exists()
        assert (project_root / "tests" / "integration" / "__init__.py").exists()
        
    finally:
        os.chdir(original_cwd)