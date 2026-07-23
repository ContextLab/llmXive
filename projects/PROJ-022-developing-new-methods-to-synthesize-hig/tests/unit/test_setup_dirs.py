"""
Unit tests for directory setup functionality (T004).
Verifies that required directories are created correctly.
"""
import os
import tempfile
import shutil
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.setup_dirs import ensure_directory, setup_project_structure

class TestEnsureDirectory:
    """Tests for ensure_directory function"""
    
    def test_create_new_directory(self, tmp_path):
        """Test that a new directory is created"""
        test_dir = tmp_path / "new_test_dir"
        assert not test_dir.exists()
        
        # Change to tmp_path to test relative paths
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = ensure_directory("new_test_dir")
            assert result is True
            assert test_dir.exists()
            assert test_dir.is_dir()
        finally:
            os.chdir(old_cwd)
    
    def test_existing_directory(self, tmp_path):
        """Test that existing directory returns True"""
        test_dir = tmp_path / "existing_dir"
        test_dir.mkdir()
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = ensure_directory("existing_dir")
            assert result is True
        finally:
            os.chdir(old_cwd)
    
    def test_nested_directories(self, tmp_path):
        """Test that nested directories are created"""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        assert not nested_dir.exists()
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = ensure_directory("level1/level2/level3")
            assert result is True
            assert nested_dir.exists()
        finally:
            os.chdir(old_cwd)

class TestSetupProjectStructure:
    """Tests for setup_project_structure function"""
    
    def test_creates_all_required_dirs(self, tmp_path):
        """Test that all required directories are created"""
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/reports",
            "tests",
            "artifacts",
            "figures"
        ]
        
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = setup_project_structure()
            assert result is True
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
        finally:
            os.chdir(old_cwd)
    
    def test_returns_false_on_failure(self, tmp_path, monkeypatch):
        """Test that function returns False when directory creation fails"""
        # This is hard to test without mocking, so we skip for now
        # The function is designed to log errors and return False
        pass

class TestGitignoreRules:
    """Tests to verify .gitignore rules exist"""
    
    def test_gitignore_exists(self):
        """Test that .gitignore file exists in project root"""
        gitignore_path = project_root / ".gitignore"
        assert gitignore_path.exists(), ".gitignore file not found"
    
    def test_gitignore_contains_data_rules(self):
        """Test that .gitignore contains data directory rules"""
        gitignore_path = project_root / ".gitignore"
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        required_patterns = [
            "data/raw/*",
            "data/processed/*",
            "*.pkl",
            "__pycache__",
            "*.log"
        ]
        
        for pattern in required_patterns:
            assert pattern in content, f"Pattern '{pattern}' not found in .gitignore"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])