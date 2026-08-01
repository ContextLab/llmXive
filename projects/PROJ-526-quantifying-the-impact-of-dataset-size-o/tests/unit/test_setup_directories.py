"""
Unit tests for the setup_directories module.
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path
from code.setup_directories import create_directories, DIRECTORIES_TO_CREATE

def test_create_directories_structure(tmp_path):
    """
    Test that create_directories creates all expected subdirectories
    under a temporary root directory.
    """
    # Arrange
    expected_dirs = [
        "code", "data", "tests", "state", "docs",
        "data/raw", "data/processed",
        "tests/contract", "tests/unit", "tests/integration",
        "state/checksums"
    ]
    
    # Act
    created_paths = create_directories(tmp_path)
    
    # Assert
    # Check that the correct number of directories were reported
    assert len(created_paths) == len(expected_dirs)
    
    # Check that each expected directory actually exists on the filesystem
    for dir_name in expected_dirs:
        target_path = tmp_path / dir_name
        assert target_path.exists(), f"Directory {target_path} was not created."
        assert target_path.is_dir(), f"Path {target_path} exists but is not a directory."

def test_create_directories_idempotent(tmp_path):
    """
    Test that running create_directories multiple times does not raise errors
    and results in the same directory structure.
    """
    # Act - run twice
    paths_first = create_directories(tmp_path)
    paths_second = create_directories(tmp_path)
    
    # Assert
    assert len(paths_first) == len(paths_second)
    assert paths_first == paths_second
    
    # Verify structure still exists
    for dir_name in DIRECTORIES_TO_CREATE:
        assert (tmp_path / dir_name).exists()