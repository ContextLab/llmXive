"""
Test suite for project structure initialization.

Verifies that the required directory tree exists as specified in T001.
"""
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

class TestProjectStructure:
    """Tests for project structure initialization."""
    
    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).resolve().parent.parent
    
    def test_required_directories_exist(self, project_root):
        """Test that all required directories from T001 exist."""
        required_dirs = [
            "code",
            "data/raw",
            "data/interim",
            "data/processed",
            "tests",
            "reports",
            "docs",
            "specs",
            "state",
            "data/figures",
        ]
        
        missing = []
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            if not dir_path.exists():
                missing.append(dir_name)
            elif not dir_path.is_dir():
                missing.append(f"{dir_name} (not a directory)")
        
        assert len(missing) == 0, f"Missing required directories: {missing}"
    
    def test_data_hierarchy(self, project_root):
        """Test that data subdirectories are correctly nested."""
        data_dirs = [
            "data/raw",
            "data/interim",
            "data/processed",
            "data/figures",
        ]
        
        for dir_name in data_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Data subdirectory missing: {dir_name}"
            assert dir_path.is_dir(), f"Data subdirectory is not a directory: {dir_name}"
    
    def test_code_directory(self, project_root):
        """Test that code directory exists."""
        code_dir = project_root / "code"
        assert code_dir.exists(), "code/ directory missing"
        assert code_dir.is_dir(), "code/ is not a directory"
    
    def test_tests_directory(self, project_root):
        """Test that tests directory exists."""
        tests_dir = project_root / "tests"
        assert tests_dir.exists(), "tests/ directory missing"
        assert tests_dir.is_dir(), "tests/ is not a directory"