import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from code.setup_data_dirs import setup_data_directories

class TestSetupDataDirs:
    """
    Unit tests for the data directory setup functionality.
    """
    
    def test_creates_data_structure(self, tmp_path):
        """Test that the function creates the required directory structure."""
        results = setup_data_directories(tmp_path)
        
        # Check we got results for all directories
        assert len(results) == 3, "Should create 3 directories (root, raw, processed)"
        
        # Check all operations succeeded
        for path, success in results:
            assert success, f"Directory creation failed for {path}"
            assert path.exists(), f"Directory does not exist: {path}"
            
        # Verify specific subdirectories exist
        data_root = tmp_path / "data"
        raw_dir = data_root / "raw"
        processed_dir = data_root / "processed"
        
        assert data_root.exists(), "Data root directory missing"
        assert raw_dir.exists(), "Raw directory missing"
        assert processed_dir.exists(), "Processed directory missing"
    
    def test_directories_are_writable(self, tmp_path):
        """Test that created directories are actually writable."""
        results = setup_data_directories(tmp_path)
        
        for path, success in results:
            if success:
                # Try to create a file in the directory
                test_file = path / "writable_test.txt"
                try:
                    test_file.write_text("test")
                    assert test_file.exists(), "Could not write to directory"
                    test_file.unlink()
                except PermissionError:
                    pytest.fail(f"Directory {path} is not writable")
    
    def test_handles_existing_directories(self, tmp_path):
        """Test that the function handles existing directories gracefully."""
        # Create directories manually first
        data_root = tmp_path / "data"
        data_root.mkdir()
        (data_root / "raw").mkdir()
        (data_root / "processed").mkdir()
        
        # Run setup again - should not fail
        results = setup_data_directories(tmp_path)
        
        for path, success in results:
            assert success, f"Failed on existing directory: {path}"
            assert path.exists(), f"Directory missing after re-run: {path}"
    
    def test_returns_correct_structure(self, tmp_path):
        """Test that the function returns the expected structure."""
        results = setup_data_directories(tmp_path)
        
        # Verify return type
        assert isinstance(results, list), "Should return a list"
        
        # Verify each item is a tuple of (Path, bool)
        for item in results:
            assert isinstance(item, tuple), "Each item should be a tuple"
            assert len(item) == 2, "Each tuple should have 2 elements"
            assert isinstance(item[0], Path), "First element should be Path"
            assert isinstance(item[1], bool), "Second element should be bool"
    
    def test_relative_path_handling(self):
        """Test that the function works with relative paths."""
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)
                # Use relative path
                results = setup_data_directories(Path("."))
                
                # Should create data/ in current directory
                data_root = Path("data")
                assert data_root.exists(), "Data root not created with relative path"
                assert (data_root / "raw").exists(), "Raw not created with relative path"
                assert (data_root / "processed").exists(), "Processed not created with relative path"
        finally:
            os.chdir(original_cwd)