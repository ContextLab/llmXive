import os
import stat
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from code_01_setup_permissions import set_restricted_permissions

def test_set_restricted_permissions_creates_555():
    """Test that the function correctly sets 555 permissions on an existing directory."""
    # Create a temporary directory to test on (we need a writable parent to create the test dir)
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_data_raw"
        test_dir.mkdir()
        
        # Ensure it has write permissions initially (it should by default)
        initial_mode = test_dir.stat().st_mode & 0o777
        assert (initial_mode & stat.S_IWUSR) != 0, "Test setup failed: directory should be writable"
        
        # Call the function
        result = set_restricted_permissions(str(test_dir))
        
        assert result is True, "Function should return True on success"
        
        # Verify permissions
        final_mode = test_dir.stat().st_mode & 0o777
        expected_mode = 0o555
        
        assert final_mode == expected_mode, f"Expected {oct(expected_mode)}, got {oct(final_mode)}"
        
        # Verify write bits are cleared
        assert (final_mode & stat.S_IWUSR) == 0, "Owner write bit should be cleared"
        assert (final_mode & stat.S_IWGRP) == 0, "Group write bit should be cleared"
        assert (final_mode & stat.S_IWOTH) == 0, "Other write bit should be cleared"

def test_set_restricted_permissions_nonexistent_path():
    """Test that the function raises FileNotFoundError for non-existent paths."""
    with pytest.raises(FileNotFoundError):
        set_restricted_permissions("/path/that/does/not/exist/12345")

def test_set_restricted_permissions_file_instead_of_dir(tmp_path):
    """Test that the function raises NotADirectoryError if path is a file."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("content")
    
    with pytest.raises(NotADirectoryError):
        set_restricted_permissions(str(test_file))

def test_set_restricted_permissions_preserves_read_execute():
    """Test that read and execute permissions are preserved/added."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_dir"
        test_dir.mkdir()
        
        set_restricted_permissions(str(test_dir))
        
        mode = test_dir.stat().st_mode & 0o777
        
        # Check read bits
        assert (mode & stat.S_IRUSR) != 0, "Owner read should be set"
        assert (mode & stat.S_IRGRP) != 0, "Group read should be set"
        assert (mode & stat.S_IROTH) != 0, "Other read should be set"
        
        # Check execute bits
        assert (mode & stat.S_IXUSR) != 0, "Owner execute should be set"
        assert (mode & stat.S_IXGRP) != 0, "Group execute should be set"
        assert (mode & stat.S_IXOTH) != 0, "Other execute should be set"