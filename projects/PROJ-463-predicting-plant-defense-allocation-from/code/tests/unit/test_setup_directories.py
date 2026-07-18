"""
Unit tests for the directory setup functionality (T007).

Verifies that the required data directory structure is created correctly
and that the setup function handles edge cases appropriately.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.setup_directories import setup_data_directories, REQUIRED_DIRS
from src.utils.config import reset_config, get_data_path

class TestDirectorySetup:
    """Tests for the directory setup functionality."""
    
    def setup_method(self):
        """Set up a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        # Reset config to use our temp directory
        reset_config()
        os.environ["DATA_PATH"] = self.temp_dir
        
    def teardown_method(self):
        """Clean up the temporary directory after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
    def test_required_dirs_constant(self):
        """Verify that REQUIRED_DIRS contains all expected subdirectories."""
        expected_dirs = {"raw", "processed", "traits", "manifests", "synthetic"}
        actual_dirs = set(REQUIRED_DIRS)
        assert expected_dirs == actual_dirs, f"Expected {expected_dirs}, got {actual_dirs}"
        
    def test_directories_created(self):
        """Test that all required directories are created."""
        data_root = setup_data_directories()
        
        # Verify the base directory exists
        assert data_root.exists(), f"Data root {data_root} does not exist"
        assert data_root.is_dir(), f"{data_root} is not a directory"
        
        # Verify all subdirectories exist
        for subdir in REQUIRED_DIRS:
            dir_path = data_root / subdir
            assert dir_path.exists(), f"Subdirectory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"
            
    def test_directories_idempotent(self):
        """Test that running setup multiple times doesn't cause errors."""
        # Run setup twice
        data_root1 = setup_data_directories()
        data_root2 = setup_data_directories()
        
        # Both should return the same path
        assert data_root1 == data_root2
        
        # All directories should still exist
        for subdir in REQUIRED_DIRS:
            assert (data_root1 / subdir).exists()
            
    def test_creates_parent_directories(self):
        """Test that parent directories are created if they don't exist."""
        # Temporarily change config to a nested path
        nested_path = Path(self.temp_dir) / "nested" / "deep"
        os.environ["DATA_PATH"] = str(nested_path)
        
        data_root = setup_data_directories()
        
        # Verify the nested structure was created
        assert data_root.exists()
        for subdir in REQUIRED_DIRS:
            assert (data_root / subdir).exists()
            
    def test_config_integration(self):
        """Test that setup uses the configured data path."""
        custom_path = Path(self.temp_dir) / "custom_data"
        os.environ["DATA_PATH"] = str(custom_path)
        
        data_root = setup_data_directories()
        
        assert str(data_root) == str(custom_path), \
            f"Expected {custom_path}, got {data_root}"
            
    def test_manifests_dir_created(self):
        """Specific test for manifests directory (needed for T011/T015)."""
        data_root = setup_data_directories()
        manifests_path = data_root / "manifests"
        
        assert manifests_path.exists()
        assert manifests_path.is_dir()
        
    def test_processed_dir_created(self):
        """Specific test for processed directory (needed for T012/T013)."""
        data_root = setup_data_directories()
        processed_path = data_root / "processed"
        
        assert processed_path.exists()
        assert processed_path.is_dir()
        
    def test_synthetic_dir_created(self):
        """Specific test for synthetic directory (needed for T015)."""
        data_root = setup_data_directories()
        synthetic_path = data_root / "synthetic"
        
        assert synthetic_path.exists()
        assert synthetic_path.is_dir()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])