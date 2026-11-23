"""
Unit tests for setup_tests_structure.py (Task T001b).
Verifies that the 'tests/' directory creation is idempotent and writable.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add parent directory to path to import setup_tests_structure
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from setup_tests_structure import ensure_dir, verify_writable


class TestDirectorySetup:
    """Test cases for directory creation and verification functions."""

    def test_ensure_dir_creates_new_directory(self, tmp_path):
        """Test that ensure_dir creates a new directory if it doesn't exist."""
        new_dir = tmp_path / "new_test_dir"
        assert not new_dir.exists()

        result = ensure_dir(new_dir)

        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_dir_idempotent(self, tmp_path):
        """Test that ensure_dir is idempotent (runs successfully twice)."""
        new_dir = tmp_path / "idempotent_test_dir"
        ensure_dir(new_dir)  # First call
        assert new_dir.exists()

        result = ensure_dir(new_dir)  # Second call

        assert result is True
        assert new_dir.exists()

    def test_verify_writable_true(self, tmp_path):
        """Test that verify_writable returns True for a writable directory."""
        assert verify_writable(tmp_path) is True

    def test_verify_writable_creates_and_removes_file(self, tmp_path):
        """Test that verify_writable actually writes and cleans up a test file."""
        test_marker = tmp_path / ".write_test_001b.tmp"
        assert not test_marker.exists()

        result = verify_writable(tmp_path)

        assert result is True
        assert not test_marker.exists()  # Should be cleaned up

    def test_verify_writable_false_on_non_existent_parent(self):
        """Test verify_writable behavior on a path where parent doesn't exist."""
        # This case is handled by ensure_dir usually, but verify_writable
        # should fail gracefully if the directory itself is missing or invalid.
        # However, the function assumes the directory exists (passed from ensure_dir).
        # If passed a non-existent path, it will fail to create the temp file.
        fake_path = Path("/non_existent_dir_12345")
        assert verify_writable(fake_path) is False

    def test_integration_main_flow(self, tmp_path, capsys):
        """Test the main logic flow using a temporary directory as the project root."""
        # We need to simulate the environment where PROJECT_ROOT is tmp_path
        # and the target is 'tests'
        import setup_tests_structure
        original_root = getattr(setup_tests_structure, 'PROJECT_ROOT', None)
        
        # Temporarily override PROJECT_ROOT
        setup_tests_structure.PROJECT_ROOT = tmp_path

        try:
            # Run main with specific arguments
            exit_code = setup_tests_structure.main(["--path", "tests"])
            
            assert exit_code == 0
            
            # Verify directory was created
            tests_dir = tmp_path / "tests"
            assert tests_dir.exists()
            assert tests_dir.is_dir()
            
            # Verify it is writable
            assert verify_writable(tests_dir) is True

        finally:
            # Restore original PROJECT_ROOT if it existed
            if original_root is not None:
                setup_tests_structure.PROJECT_ROOT = original_root
            else:
                if hasattr(setup_tests_structure, 'PROJECT_ROOT'):
                    delattr(setup_tests_structure, 'PROJECT_ROOT')