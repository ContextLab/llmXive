"""
Unit tests for the data directory setup script.
"""
import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import setup_data_directories

class TestSetupDataDirs:
    """Tests for the setup_data_directories function."""

    def test_creates_required_directories(self, tmp_path):
        """Test that the function creates data/raw and data/processed."""
        result_dirs = setup_data_directories(tmp_path)
        
        # Check that we got 3 directories
        assert len(result_dirs) == 3
        
        # Check specific directory names
        dir_names = [d.name for d in result_dirs]
        assert "data" in dir_names
        assert "raw" in dir_names
        assert "processed" in dir_names
        
        # Check paths exist
        for d in result_dirs:
            assert d.exists()
            assert d.is_dir()

    def test_verifies_writability(self, tmp_path):
        """Test that the function verifies directory writability."""
        # This should not raise an exception if directories are writable
        result_dirs = setup_data_directories(tmp_path)
        
        # All directories should be writable (no exception raised)
        for d in result_dirs:
            test_file = d / ".write_test_verify"
            try:
                with open(test_file, 'w') as f:
                    f.write("verify")
                test_file.unlink()
            except IOError:
                pytest.fail(f"Directory {d} is not writable")

    def test_handles_existing_directories(self, tmp_path):
        """Test that the function handles pre-existing directories."""
        # Create the directories first
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "raw").mkdir()
        (data_dir / "processed").mkdir()
        
        # Should not raise an exception
        result_dirs = setup_data_directories(tmp_path)
        
        # Should still return 3 directories
        assert len(result_dirs) == 3

    def test_raises_on_non_writable_directory(self, tmp_path):
        """Test that the function raises on non-writable directories."""
        # Create a read-only directory
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        data_dir.chmod(0o444)  # Read-only
        
        try:
            with pytest.raises(RuntimeError) as exc_info:
                setup_data_directories(tmp_path)
            
            assert "not writable" in str(exc_info.value).lower()
        finally:
            # Restore permissions so cleanup works
            data_dir.chmod(0o755)

    def test_creates_nested_structure(self, tmp_path):
        """Test that the function creates nested directories if they don't exist."""
        # Remove any existing data dir to ensure fresh creation
        data_dir = tmp_path / "data"
        if data_dir.exists():
            shutil.rmtree(data_dir)
        
        result_dirs = setup_data_directories(tmp_path)
        
        # Check that all three levels exist
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        
        # Check they are in the result
        dir_paths = [str(d) for d in result_dirs]
        assert str(tmp_path / "data") in dir_paths
        assert str(tmp_path / "data" / "raw") in dir_paths
        assert str(tmp_path / "data" / "processed") in dir_paths