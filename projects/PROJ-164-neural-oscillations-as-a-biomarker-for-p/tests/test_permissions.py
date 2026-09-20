import os
import stat
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test
from code.setup_permissions import set_restricted_permissions


def test_set_restricted_permissions_success():
    """Test that set_restricted_permissions correctly sets 555 on an existing directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_dir"
        test_dir.mkdir()
        
        # Initially it should be writable (usually 755 or 700 depending on umask)
        initial_mode = test_dir.stat().st_mode & 0o777
        
        # Set permissions
        result = set_restricted_permissions(test_dir)
        
        assert result is True
        
        # Verify final mode is 555
        final_mode = test_dir.stat().st_mode & 0o777
        assert final_mode == 0o555, f"Expected 0o555, got {oct(final_mode)}"


def test_set_restricted_permissions_nonexistent_path():
    """Test that FileNotFoundError is raised for non-existent paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent = Path(tmpdir) / "does_not_exist"
        
        with pytest.raises(FileNotFoundError):
            set_restricted_permissions(non_existent)


def test_set_restricted_permissions_file_instead_of_dir():
    """Test that NotADirectoryError is raised if path is a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test_file.txt"
        test_file.write_text("content")
        
        with pytest.raises(NotADirectoryError):
            set_restricted_permissions(test_file)
