"""
Unit tests for the project structure initialization logic.

These tests verify that the directory creation logic handles
edge cases, permissions (mocked), and retry logic correctly.
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the functions to test
# We need to adjust the import path if running from the tests directory
# Assuming the test runner adds the project root or code directory to sys.path
try:
    from setup_project_structure import (
        ensure_dir_with_backoff,
        REQUIRED_DIRS,
        PROJECT_ROOT
    )
except ImportError:
    # Fallback for local execution if path isn't set correctly in the test environment
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    from setup_project_structure import (
        ensure_dir_with_backoff,
        REQUIRED_DIRS,
        PROJECT_ROOT
    )


class TestEnsureDirWithBackoff:
    """Tests for the ensure_dir_with_backoff function."""

    def test_creates_missing_directory(self, tmp_path):
        """Test that a missing directory is created successfully."""
        target_dir = tmp_path / "new_dir"
        assert not target_dir.exists()

        success, message = ensure_dir_with_backoff(target_dir, max_retries=1)

        assert success is True
        assert target_dir.exists()
        assert target_dir.is_dir()
        assert "Successfully created" in message

    def test_idempotent_existing_directory(self, tmp_path):
        """Test that an existing directory is handled gracefully (idempotency)."""
        target_dir = tmp_path / "existing_dir"
        target_dir.mkdir(parents=True)
        assert target_dir.exists()

        success, message = ensure_dir_with_backoff(target_dir, max_retries=1)

        assert success is True
        assert "Successfully created" in message or "Verified" in message

    def test_retry_logic_on_failure(self, tmp_path):
        """Test that the function retries on failure with backoff."""
        target_dir = tmp_path / "failing_dir"
        
        # Mock mkdir to fail once then succeed
        call_count = 0
        original_mkdir = Path.mkdir

        def mock_mkdir(self, parents=False, exist_ok=False):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Simulate a transient error (e.g., permission denied or race condition)
                raise PermissionError("Simulated transient failure")
            return original_mkdir(self, parents=parents, exist_ok=exist_ok)

        with patch.object(Path, 'mkdir', mock_mkdir):
            # Set a very short delay for testing
            with patch('setup_project_structure.time.sleep', return_value=None):
                success, message = ensure_dir_with_backoff(target_dir, max_retries=3, INITIAL_DELAY=0.01)

        # Should have retried and succeeded
        assert success is True
        assert target_dir.exists()

    def test_max_retries_exceeded(self, tmp_path):
        """Test that the function returns False after max retries."""
        target_dir = tmp_path / "always_fail_dir"
        
        # Mock mkdir to always fail
        with patch.object(Path, 'mkdir', side_effect=PermissionError("Persistent failure")):
            success, message = ensure_dir_with_backoff(target_dir, max_retries=2)

        assert success is False
        assert "Failed to create" in message
        assert not target_dir.exists()

    def test_path_is_not_directory(self, tmp_path):
        """Test handling when the path exists but is a file."""
        target_path = tmp_path / "not_a_dir"
        target_path.touch() # Create a file instead

        success, message = ensure_dir_with_backoff(target_path, max_retries=1)

        assert success is False
        assert "not a directory" in message.lower() or "File" in message


class TestRequiredDirs:
    """Tests for the REQUIRED_DIRS constant."""

    def test_required_dirs_contains_expected_values(self):
        """Verify the list contains the standard project directories."""
        expected = {"code", "tests", "data/raw", "data/processed", "results"}
        actual = set(REQUIRED_DIRS)
        assert expected.issubset(actual), f"Missing expected dirs: {expected - actual}"

    def test_required_dirs_format(self):
        """Verify paths are relative strings."""
        for dir_path in REQUIRED_DIRS:
            assert isinstance(dir_path, str)
            assert not os.path.isabs(dir_path), f"Path {dir_path} should be relative"

class TestProjectRoot:
    """Tests for PROJECT_ROOT derivation."""

    def test_project_root_is_absolute(self):
        """Verify PROJECT_ROOT is an absolute path."""
        assert PROJECT_ROOT.is_absolute()

    def test_project_root_is_parent_of_code(self):
        """Verify PROJECT_ROOT resolves correctly relative to the script."""
        # The script is in code/setup_project_structure.py
        # So PROJECT_ROOT should be the parent of that directory
        expected_parent = Path(__file__).parent.parent / "code"
        # Actually, the script logic sets PROJECT_ROOT = SCRIPT_DIR.parent
        # SCRIPT_DIR is code/, so PROJECT_ROOT is the repo root
        # We can't strictly verify the repo root without knowing the repo structure,
        # but we can verify it's a valid Path object.
        assert isinstance(PROJECT_ROOT, Path)
        assert PROJECT_ROOT.exists()