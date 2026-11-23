import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import create_directory


def test_create_directory_new():
    """Test creating a new directory."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "new_dir"
        create_directory(test_path, "test directory")
        assert test_path.exists()
        assert test_path.is_dir()


def test_create_directory_exists():
    """Test creating a directory that already exists."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "existing_dir"
        test_path.mkdir()
        # Should not raise
        create_directory(test_path, "existing test directory")
        assert test_path.exists()


def test_create_directory_verification():
    """Test that verification raises if creation fails."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file where we want a directory
        test_path = Path(tmpdir) / "file_instead_of_dir"
        test_path.touch()
        
        with pytest.raises(RuntimeError, match="Directory creation failed"):
            create_directory(test_path, "should fail")