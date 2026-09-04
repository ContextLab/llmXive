"""
Unit tests for the setup_data_dirs module.

Tests:
- Directory creation
- Directory writability verification
- Error handling for permission issues
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import setup_data_directories


def test_setup_data_directories_creates_structure():
    """Test that the function creates the required directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        created_dirs = setup_data_directories(base_dir)
        
        # Check that 3 directories were created/verified
        assert len(created_dirs) == 3
        
        # Check specific directories
        data_dir = base_dir / "data"
        raw_dir = base_dir / "data" / "raw"
        processed_dir = base_dir / "data" / "processed"
        
        assert data_dir in created_dirs
        assert raw_dir in created_dirs
        assert processed_dir in created_dirs
        
        # Verify they actually exist on disk
        assert data_dir.exists()
        assert raw_dir.exists()
        assert processed_dir.exists()


def test_setup_data_directories_handles_existing():
    """Test that the function handles existing directories gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        
        # Create the directories manually first
        (base_dir / "data").mkdir()
        (base_dir / "data" / "raw").mkdir()
        (base_dir / "data" / "processed").mkdir()
        
        # This should not raise an error
        created_dirs = setup_data_directories(base_dir)
        
        assert len(created_dirs) == 3
        assert all(d.exists() for d in created_dirs)


def test_setup_data_directories_writability():
    """Test that the function verifies writability."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        
        # This should succeed and verify writability
        created_dirs = setup_data_directories(base_dir)
        
        # Verify no leftover test files
        for d in created_dirs:
            test_file = d / ".write_test"
            assert not test_file.exists(), "Test file was not cleaned up"


def test_setup_data_directories_permission_error():
    """Test that the function raises RuntimeError on permission errors."""
    # This test is tricky to run in all environments, so we skip if not root
    # We create a read-only directory to simulate the error
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        data_dir = base_dir / "data"
        data_dir.mkdir()
        
        # Make the directory read-only (only works if we are not root)
        if os.geteuid() != 0:
            data_dir.chmod(0o444)
            
            try:
                with pytest.raises(RuntimeError) as exc_info:
                    setup_data_directories(base_dir)
                
                assert "Permission denied" in str(exc_info.value) or "not writable" in str(exc_info.value)
            finally:
                # Restore permissions so cleanup works
                data_dir.chmod(0o755)