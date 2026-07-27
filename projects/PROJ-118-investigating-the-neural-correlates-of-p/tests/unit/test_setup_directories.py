import os
import tempfile
from pathlib import Path
import pytest

from code.setup_directories import setup_directories


def test_setup_directories_creates_all_required_paths():
    """Test that setup_directories creates all required directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_directories(tmpdir)
        
        project_root = Path(tmpdir)
        
        # Check all required directories exist
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "tests",
            "results",
            "results/plots",
            "specs",
        ]
        
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"
        
        # Check that .gitkeep files exist
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            gitkeep_path = full_path / ".gitkeep"
            assert gitkeep_path.exists(), f".gitkeep not found in {dir_path}"
            assert gitkeep_path.is_file(), f".gitkeep in {dir_path} is not a file"


def test_setup_directories_idempotent():
    """Test that running setup_directories twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run twice
        setup_directories(tmpdir)
        setup_directories(tmpdir)
        
        # Verify directories still exist
        project_root = Path(tmpdir)
        assert (project_root / "data/raw").exists()
        assert (project_root / "data/processed").exists()
        assert (project_root / "code").exists()
        assert (project_root / "tests").exists()
        assert (project_root / "results").exists()


def test_setup_directories_creates_gitkeep_content():
    """Test that .gitkeep files have appropriate content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_directories(tmpdir)
        
        project_root = Path(tmpdir)
        gitkeep_path = project_root / "data/raw" / ".gitkeep"
        
        content = gitkeep_path.read_text()
        assert "git" in content.lower(), ".gitkeep should mention git"
        assert len(content) > 0, ".gitkeep should not be empty"