"""
Unit tests for the directory setup utility.
"""
import pytest
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import PROJECT_ROOT
from code.utils.directory_setup import create_directory_structure, REQUIRED_DIRS

def test_required_dirs_defined():
    """Test that required directories are defined."""
    assert len(REQUIRED_DIRS) > 0, "REQUIRED_DIRS should not be empty"
    assert "data/raw" in REQUIRED_DIRS
    assert "data/processed" in REQUIRED_DIRS
    assert "data/validation" in REQUIRED_DIRS
    assert "results" in REQUIRED_DIRS

def test_create_directory_structure_creates_dirs(tmp_path, monkeypatch):
    """
    Test that create_directory_structure creates the expected directories.
    Uses a temporary path to avoid modifying the actual project structure.
    """
    # Mock PROJECT_ROOT to point to a temporary directory
    monkeypatch.setattr("code.utils.directory_setup.PROJECT_ROOT", str(tmp_path))

    success = create_directory_structure()

    assert success is True, "Directory creation should succeed in a temp directory"

    for dir_path_str in REQUIRED_DIRS:
        expected_path = tmp_path / dir_path_str
        assert expected_path.exists(), f"Directory {expected_path} should exist"
        assert expected_path.is_dir(), f"{expected_path} should be a directory"

def test_create_directory_structure_idempotent(tmp_path, monkeypatch):
    """
    Test that running create_directory_structure twice doesn't cause errors.
    """
    monkeypatch.setattr("code.utils.directory_setup.PROJECT_ROOT", str(tmp_path))

    # Run twice
    success1 = create_directory_structure()
    success2 = create_directory_structure()

    assert success1 is True
    assert success2 is True

    # Verify directories still exist
    for dir_path_str in REQUIRED_DIRS:
        expected_path = tmp_path / dir_path_str
        assert expected_path.exists()