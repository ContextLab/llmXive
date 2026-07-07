"""
Unit tests for T001: Project directory structure creation.
Verifies that the setup script creates all required directories.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path to import the setup script module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

def test_required_directories_exist():
    """Test that all required directories are created by the setup script."""
    # Create a temporary directory to simulate project root
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Mock the project root structure for testing
        # We'll manually create the 'code' dir so the script thinks it's in the right place
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        # Import and run the setup logic directly
        from setup_project_structure import REQUIRED_DIRS, create_directories
        
        create_directories(tmp_path)
        
        # Verify all directories were created
        for dir_name in REQUIRED_DIRS:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"

def test_nested_directories_created():
    """Test that nested directories (e.g., tests/unit) are created correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        from setup_project_structure import create_directories
        create_directories(tmp_path)
        
        # Check specific nested directories
        nested_dirs = [
            "tests/unit",
            "tests/integration", 
            "tests/contract",
            "data/raw",
            "data/processed",
            "data/external",
        ]
        
        for dir_name in nested_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Nested directory {dir_path} was not created"

def test_idempotent_creation():
    """Test that running the script twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        from setup_project_structure import create_directories
        
        # Run twice
        create_directories(tmp_path)
        create_directories(tmp_path)
        
        # Should still exist
        assert (tmp_path / "code").exists()
        assert (tmp_path / "data").exists()
        assert (tmp_path / "tests").exists()