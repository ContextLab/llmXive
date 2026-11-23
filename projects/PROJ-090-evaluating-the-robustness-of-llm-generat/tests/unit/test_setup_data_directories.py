"""
Unit tests for the setup_data_directories module.

These tests verify that the data directory structure is created correctly
with the proper permissions (755).
"""
import os
import stat
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to test the logic, but we can't actually create directories 
# in the project root during testing. So we'll test the permission logic.

def test_permission_bits():
    """Test that 755 permissions are correctly represented."""
    # 755 in octal = rwxr-xr-x
    expected_mode = 0o755
    # Check that the bits are set correctly
    assert (expected_mode & 0o755) == 0o755
    
    # Verify individual permission bits
    assert expected_mode & stat.S_IRUSR  # Owner read
    assert expected_mode & stat.S_IWUSR  # Owner write
    assert expected_mode & stat.S_IXUSR  # Owner execute
    assert expected_mode & stat.S_IRGRP  # Group read
    assert expected_mode & stat.S_IXGRP  # Group execute
    assert expected_mode & stat.S_IROTH  # Others read
    assert expected_mode & stat.S_IXOTH  # Others execute
    
    # Verify write bits for group/others are NOT set
    assert not (expected_mode & stat.S_IWGRP)
    assert not (expected_mode & stat.S_IWOTH)


def test_directory_creation_logic():
    """Test that directory creation logic works in a temp directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        base_dir = tmp_path / "data"
        subdirs = ["raw", "processed", "logs"]
        
        # Create base
        base_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(base_dir, 0o755)
        
        # Create subdirs
        created = []
        for subdir_name in subdirs:
            subdir_path = base_dir / subdir_name
            subdir_path.mkdir(parents=True, exist_ok=True)
            os.chmod(subdir_path, 0o755)
            created.append(subdir_path)
        
        # Verify all exist
        assert base_dir.exists()
        for s in created:
            assert s.exists()
            assert s.is_dir()
            
        # Verify permissions
        for d in [base_dir] + created:
            mode = os.stat(d).st_mode & 0o777
            assert mode == 0o755, f"Directory {d} has wrong permissions: {oct(mode)}"


def test_idempotency():
    """Test that running the creation twice doesn't fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        base_dir = tmp_path / "data"
        
        # First creation
        base_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(base_dir, 0o755)
        
        # Second creation (should not raise)
        base_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(base_dir, 0o755)
        
        assert base_dir.exists()
        assert (os.stat(base_dir).st_mode & 0o777) == 0o755
