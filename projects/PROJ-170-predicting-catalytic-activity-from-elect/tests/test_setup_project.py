import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project import create_directories, verify_directories, create_init_files, REQUIRED_DIRS
from config import get_project_root

class TestSetupProject:
    @pytest.fixture(autouse=True)
    def setup_temp_dir(self, tmp_path):
        """Mock get_project_root to return a temporary directory for safe testing."""
        with patch('setup_project.get_project_root', return_value=tmp_path):
            yield tmp_path

    def test_create_directories(self, setup_temp_dir):
        """Test that create_directories actually creates the required folders."""
        create_directories()
        
        for dir_name in REQUIRED_DIRS:
            expected_path = setup_temp_dir / dir_name
            assert expected_path.exists(), f"Directory {dir_name} was not created."
            assert expected_path.is_dir(), f"{dir_name} exists but is not a directory."

    def test_verify_directories_success(self, setup_temp_dir):
        """Test verify_directories passes when all directories exist."""
        # Ensure directories exist first
        create_directories()
        
        # This should not raise
        result = verify_directories()
        assert result is True

    def test_verify_directories_failure(self, setup_temp_dir):
        """Test verify_directories fails loudly when a directory is missing."""
        # Do not create directories
        with pytest.raises(FileNotFoundError) as exc_info:
            verify_directories()
        
        assert "missing" in str(exc_info.value).lower()

    def test_create_init_files(self, setup_temp_dir):
        """Test that __init__.py files are created in package directories."""
        create_directories()
        create_init_files()
        
        # Check specific expected __init__.py files
        expected_inits = [
            setup_temp_dir / "code" / "__init__.py",
            setup_temp_dir / "tests" / "__init__.py",
            setup_temp_dir / "state" / "projects" / "__init__.py",
            setup_temp_dir / "code" / "models" / "__init__.py",
        ]
        
        for init_path in expected_inits:
            assert init_path.exists(), f"__init__.py missing at {init_path}"
            assert init_path.is_file(), f"{init_path} is not a file"
    
    def test_create_init_files_nested(self, setup_temp_dir):
        """Test that __init__.py files are created in nested directories."""
        create_directories()
        # Manually create a nested dir inside code to test recursion
        nested = setup_temp_dir / "code" / "submodule"
        nested.mkdir()
        
        create_init_files()
        
        assert (nested / "__init__.py").exists()