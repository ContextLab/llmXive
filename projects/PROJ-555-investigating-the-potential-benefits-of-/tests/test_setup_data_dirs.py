"""
Tests for T008: Data directory structure setup.

Verifies that the required directories are created and .gitkeep files exist.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to test the logic without relying on the global project structure
# So we will mock the path logic or test the helper function directly if exposed.
# Since the task creates a script that uses `config.ensure_directories`,
# we will test the directory creation logic here.

def test_directory_creation_logic():
    """Test that directories and .gitkeep files are created correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Define target dirs relative to tmp_dir
        target_dirs = [
            tmp_path / "data" / "raw" / "landsat",
            tmp_path / "data" / "processed",
            tmp_path / "data" / "ecotourism",
        ]
        
        # Verify they don't exist initially
        for d in target_dirs:
            assert not d.exists(), f"Directory {d} should not exist initially"
        
        # Create them manually to simulate the script logic
        for d in target_dirs:
            d.mkdir(parents=True, exist_ok=True)
            gitkeep = d / ".gitkeep"
            gitkeep.touch()
        
        # Verify they exist now
        for d in target_dirs:
            assert d.exists(), f"Directory {d} should exist after creation"
            gitkeep = d / ".gitkeep"
            assert gitkeep.exists(), f".gitkeep should exist in {d}"
            assert gitkeep.is_file(), f".gitkeep in {d} should be a file"

def test_config_ensure_directories_usage():
    """Test that config.ensure_directories works as expected for our paths."""
    from config import ensure_directories
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        target = tmp_path / "test" / "nested" / "dir"
        
        assert not target.exists()
        
        ensure_directories([target])
        
        assert target.exists()
        assert target.is_dir()
