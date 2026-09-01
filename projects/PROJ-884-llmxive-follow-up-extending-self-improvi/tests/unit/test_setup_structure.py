"""
Unit tests for the setup_structure module.
Verifies that the code directory hierarchy is created correctly and is writable.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the project root to the path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.setup_structure import setup_code_directories, REQUIRED_SUBDIRS

def test_setup_creates_directories():
    """Test that setup_code_directories creates all required subdirectories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        created_dirs = setup_code_directories(base_path)

        # Check that the code directory was created
        code_dir = base_path / "code"
        assert code_dir.exists(), "Base 'code' directory was not created"
        assert code_dir.is_dir(), "'code' is not a directory"

        # Check that all required subdirectories were created
        for subdir_name in REQUIRED_SUBDIRS:
            subdir_path = code_dir / subdir_name
            assert subdir_path.exists(), f"Subdirectory '{subdir_name}' was not created"
            assert subdir_path.is_dir(), f"'{subdir_name}' is not a directory"

        # Check that the returned list matches the created directories
        assert len(created_dirs) == len(REQUIRED_SUBDIRS)
        for subdir_name in REQUIRED_SUBDIRS:
            assert base_path / "code" / subdir_name in created_dirs

def test_setup_verifies_writability():
    """Test that setup_code_directories verifies writability of all directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        # This should not raise an exception if directories are writable
        try:
            setup_code_directories(base_path)
        except RuntimeError as e:
            pytest.fail(f"setup_code_directories raised RuntimeError unexpectedly: {e}")

        # Verify we can actually write files to the created directories
        code_dir = base_path / "code"
        for subdir_name in REQUIRED_SUBDIRS:
            subdir_path = code_dir / subdir_name
            test_file = subdir_path / "test_write_verification.txt"
            try:
                test_file.write_text("verification content")
                assert test_file.read_text() == "verification content"
                test_file.unlink()
            except OSError as e:
                pytest.fail(f"Could not write to {subdir_path}: {e}")

def test_setup_handles_existing_directories():
    """Test that setup_code_directories handles existing directories gracefully."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        code_dir = base_path / "code"
        
        # Pre-create the code directory
        code_dir.mkdir()
        
        # Pre-create one subdirectory
        pre_created = code_dir / REQUIRED_SUBDIRS[0]
        pre_created.mkdir()
        
        # This should not fail even though some directories already exist
        created_dirs = setup_code_directories(base_path)
        
        # All directories should still be present
        for subdir_name in REQUIRED_SUBDIRS:
            subdir_path = code_dir / subdir_name
            assert subdir_path.exists()

def test_required_subdirs_defined():
    """Test that REQUIRED_SUBDIRS contains the expected directories."""
    expected_dirs = {"dataset", "symbolic", "bes", "analysis", "utils"}
    assert set(REQUIRED_SUBDIRS) == expected_dirs, f"REQUIRED_SUBDIRS mismatch: {REQUIRED_SUBDIRS}"