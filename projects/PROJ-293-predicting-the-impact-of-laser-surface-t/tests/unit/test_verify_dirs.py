"""
Unit tests for verify_dirs module.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.verify_dirs import ensure_directory


class TestEnsureDirectory:
    """Tests for the ensure_directory function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_existing_directory_returns_true(self):
        """Test that existing directory returns True."""
        test_dir = Path("test_existing")
        test_dir.mkdir()
        
        result = ensure_directory(str(test_dir))
        
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_missing_directory_created(self):
        """Test that missing directory is created when create_if_missing=True."""
        test_dir = Path("test_new_dir")
        
        assert not test_dir.exists()
        
        result = ensure_directory(str(test_dir), create_if_missing=True)
        
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_missing_directory_not_created(self):
        """Test that missing directory is not created when create_if_missing=False."""
        test_dir = Path("test_no_create")
        
        assert not test_dir.exists()
        
        result = ensure_directory(str(test_dir), create_if_missing=False)
        
        assert result is False
        assert not test_dir.exists()
    
    def test_nested_directory_creation(self):
        """Test that nested directories are created with parents=True."""
        test_dir = Path("parent/child/grandchild")
        
        result = ensure_directory(str(test_dir), create_if_missing=True)
        
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_path_not_a_directory_returns_false(self):
        """Test that path existing as file returns False."""
        test_file = Path("test_file.txt")
        test_file.touch()
        
        result = ensure_directory(str(test_file))
        
        assert result is False
    
    def test_absolute_path_handling(self):
        """Test that absolute paths are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            abs_path = Path(tmpdir) / "absolute_test"
            
            result = ensure_directory(str(abs_path), create_if_missing=True)
            
            assert result is True
            assert abs_path.exists()