"""
Tests for the setup_directories module.
Verifies that the project structure is created correctly.
"""
import os
import tempfile
from pathlib import Path
import pytest
import shutil

# We need to import the logic from setup_directories but we need to mock the paths
# to avoid modifying the actual project structure during tests.
# We will test the logic by passing temporary paths.

from setup_directories import ensure_directory

class TestEnsureDirectory:
    def test_create_new_directory(self, tmp_path):
        """Test creating a new directory."""
        new_dir = tmp_path / "new" / "nested" / "dir"
        assert not new_dir.exists()
        result = ensure_directory(new_dir)
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_existing_directory(self, tmp_path):
        """Test that existing directory returns True and doesn't error."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        result = ensure_directory(existing_dir)
        assert result is True
        assert existing_dir.exists()

    def test_create_multiple_times(self, tmp_path):
        """Test idempotency of directory creation."""
        target = tmp_path / "test_dir"
        assert ensure_directory(target)
        assert ensure_directory(target)
        assert target.exists()

# Integration style test for the structure logic (mocked)
def test_structure_logic():
    """
    Test the logic of directory creation without touching the real file system.
    We create a temp root and verify the relative paths are constructed correctly.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        project_root = root / "projects" / "PROJ-800-assessing-parcellation-sensitivity-of-hu"
        
        # Simulate the list of directories
        standard_dirs = [
            "data/raw",
            "data/processed",
            "data/results",
            "code",
            "tests",
        ]
        
        for subdir in standard_dirs:
            full_path = project_root / subdir
            ensure_directory(full_path)
            assert full_path.exists(), f"Failed to create {subdir}"
        
        # Verify specific nested structure
        assert (project_root / "data" / "raw").is_dir()
        assert (project_root / "data" / "processed").is_dir()
        assert (project_root / "data" / "results").is_dir()
        assert (project_root / "code").is_dir()
        assert (project_root / "tests").is_dir()
