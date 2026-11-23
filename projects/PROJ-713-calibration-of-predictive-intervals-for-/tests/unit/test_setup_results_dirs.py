"""
Unit tests for the results directory setup (T001e).
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from setup_results_dirs import ensure_dir
from utils.exceptions import ConfigurationError


class TestEnsureDir:
    """Tests for the ensure_dir function."""

    def test_creates_missing_directory(self, tmp_path):
        """Test that a missing directory is created."""
        new_dir = tmp_path / "new_results_dir"
        assert not new_dir.exists()
        
        result = ensure_dir(new_dir)
        
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_idempotent_existing_directory(self, tmp_path):
        """Test that existing directory is handled idempotently."""
        existing_dir = tmp_path / "existing_dir"
        existing_dir.mkdir()
        
        result = ensure_dir(existing_dir)
        
        assert result is True
        assert existing_dir.exists()

    def test_returns_false_if_path_is_file(self, tmp_path):
        """Test that function returns False if path exists as a file."""
        file_path = tmp_path / "not_a_dir"
        file_path.touch()
        
        result = ensure_dir(file_path)
        
        assert result is False

    def test_returns_false_if_not_writable(self, tmp_path):
        """Test that function returns False if directory is not writable."""
        # Create a directory and make it read-only (if permissions allow)
        # Note: This test might behave differently on Windows vs Unix
        # We simulate the check by mocking the touch operation if needed,
        # but for now, we rely on the logic inside ensure_dir.
        # On Unix, we can try to remove write permissions.
        
        read_only_dir = tmp_path / "readonly_dir"
        read_only_dir.mkdir()
        
        # Remove write permissions
        os.chmod(read_only_dir, 0o444)
        
        try:
            result = ensure_dir(read_only_dir)
            # If we are root, we might still be able to write, so result might be True
            # If not root, result should be False
            if os.geteuid() != 0:
                assert result is False
            else:
                assert result is True
        finally:
            # Restore permissions for cleanup
            os.chmod(read_only_dir, 0o755)

    def test_returns_true_for_valid_writable_directory(self, tmp_path):
        """Test that a valid, writable directory returns True."""
        valid_dir = tmp_path / "valid_dir"
        valid_dir.mkdir()
        
        result = ensure_dir(valid_dir)
        
        assert result is True