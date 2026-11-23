import os
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add the project code directory to the path for imports
# Assuming tests are run from the project root or we adjust sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from setup_directories import ensure_dir, create_gitkeep, create_gitignore
from config import get_project_root

def test_ensure_dir_creates_directory():
    """Test that ensure_dir creates a new directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "new_dir"
        assert not test_dir.exists()
        ensure_dir(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()

def test_ensure_dir_existing_directory():
    """Test that ensure_dir does not fail on existing directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        ensure_dir(test_dir)
        assert test_dir.exists()

def test_create_gitkeep():
    """Test that create_gitkeep creates a .gitkeep file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_dir"
        test_dir.mkdir()
        gitkeep_file = test_dir / ".gitkeep"
        
        assert not gitkeep_file.exists()
        create_gitkeep(test_dir)
        assert gitkeep_file.exists()
        assert gitkeep_file.is_file()

def test_create_gitignore():
    """Test that create_gitignore creates a .gitignore file with content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_dir"
        test_dir.mkdir()
        gitignore_file = test_dir / ".gitignore"
        content = "*.tmp\n"
        
        assert not gitignore_file.exists()
        create_gitignore(test_dir, content)
        assert gitignore_file.exists()
        assert gitignore_file.read_text() == content

def test_create_gitignore_skips_existing():
    """Test that create_gitignore does not overwrite existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_dir"
        test_dir.mkdir()
        gitignore_file = test_dir / ".gitignore"
        original_content = "original\n"
        gitignore_file.write_text(original_content)
        
        create_gitignore(test_dir, "new_content\n")
        assert gitignore_file.read_text() == original_content

def test_main_creates_expected_structure():
    """
    Test that main() creates the expected directory structure relative to project root.
    Note: This test modifies the actual project structure, so it should be run carefully
    or mocked in a CI environment. For safety, we mock get_project_root.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the project root
        import config
        original_get_project_root = config.get_project_root
        config.get_project_root = lambda: Path(tmpdir)
        
        try:
            from setup_directories import main
            main()
            
            # Verify directories exist
            data_raw = Path(tmpdir) / "data" / "raw"
            data_processed = Path(tmpdir) / "data" / "processed"
            artifacts_dir = Path(tmpdir) / "artifacts"
            
            assert data_raw.exists()
            assert data_processed.exists()
            assert artifacts_dir.exists()
            
            # Verify .gitkeep files exist
            assert (data_raw / ".gitkeep").exists()
            assert (data_processed / ".gitkeep").exists()
            assert (artifacts_dir / ".gitkeep").exists()
            
            # Verify .gitignore files exist
            assert (data_raw / ".gitignore").exists()
            assert (data_processed / ".gitignore").exists()
            assert (artifacts_dir / ".gitignore").exists()
            
        finally:
            # Restore original function
            config.get_project_root = original_get_project_root
