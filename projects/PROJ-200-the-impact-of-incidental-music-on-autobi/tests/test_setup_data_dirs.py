import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# We need to test the logic, but since the task is about creating directories,
# we will mock the get_project_root to use a temporary directory.

def test_setup_data_directories_creates_structure():
    """Test that setup_data_directories creates the required structure."""
    from setup_data_dirs import setup_data_directories
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Mock the config to return our temp directory as project root
        with patch('setup_data_dirs.get_project_root', return_value=tmp_path):
            # Also patch get_project_root inside the module if it was imported
            # but since we patch the function used inside the module, it should work.
            # However, to be safe, we patch the import in the module namespace
            with patch('setup_data_dirs.get_project_root', return_value=tmp_path):
                result = setup_data_directories()
                
                assert result is True
                
                # Check directories exist
                assert (tmp_path / "data" / "raw").exists()
                assert (tmp_path / "data" / "processed").exists()
                assert (tmp_path / "data" / "final").exists()
                
                # Check .gitkeep files exist and are not empty (or at least exist)
                assert (tmp_path / "data" / "raw" / ".gitkeep").exists()
                assert (tmp_path / "data" / "processed" / ".gitkeep").exists()
                assert (tmp_path / "data" / "final" / ".gitkeep").exists()

def test_setup_data_directories_idempotent():
    """Test that running the function twice doesn't raise errors."""
    from setup_data_dirs import setup_data_directories
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with patch('setup_data_dirs.get_project_root', return_value=tmp_path):
            # Run twice
            result1 = setup_data_directories()
            result2 = setup_data_directories()
            
            assert result1 is True
            assert result2 is True