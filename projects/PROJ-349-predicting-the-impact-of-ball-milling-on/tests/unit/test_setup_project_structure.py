"""
Unit tests for the project structure setup script.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from setup_project_structure import setup_directories


class TestSetupProjectStructure:
    """Test cases for setup_directories function."""

    def test_creates_all_required_directories(self):
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock the __file__ path to be inside our temp directory
            with patch('setup_project_structure.Path') as mock_path:
                mock_root = MagicMock()
                mock_root.__truediv__.return_value = Path(tmp_dir)
                mock_path.return_value = mock_root
                
                # Actually create the structure in the temp dir
                # We need to bypass the mock for the actual creation
                original_cwd = os.getcwd()
                os.chdir(tmp_dir)
                
                try:
                    # Run the setup
                    created = setup_directories()
                    
                    # Verify directories exist
                    expected_dirs = [
                        "src",
                        "tests",
                        "data/raw",
                        "data/processed",
                        "data/splits",
                        "results",
                        "contracts",
                        ".github/workflows",
                    ]
                    
                    for dir_name in expected_dirs:
                        dir_path = Path(tmp_dir) / dir_name
                        assert dir_path.exists(), f"Directory {dir_name} was not created"
                        assert dir_path.is_dir(), f"{dir_name} is not a directory"
                finally:
                    os.chdir(original_cwd)

    def test_creates_gitkeep_files(self):
        """Test that .gitkeep files are created in each directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_cwd = os.getcwd()
            os.chdir(tmp_dir)
            
            try:
                setup_directories()
                
                # Check for .gitkeep in key directories
                key_dirs = [
                    "src",
                    "tests",
                    "data/raw",
                    "results",
                    "contracts",
                ]
                
                for dir_name in key_dirs:
                    gitkeep_path = Path(tmp_dir) / dir_name / ".gitkeep"
                    assert gitkeep_path.exists(), f".gitkeep not found in {dir_name}"
            finally:
                os.chdir(original_cwd)

    def test_creates_init_files(self):
        """Test that __init__.py files are created in src and tests."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_cwd = os.getcwd()
            os.chdir(tmp_dir)
            
            try:
                setup_directories()
                
                # Check for __init__.py in src and tests
                for pkg_name in ["src", "tests"]:
                    init_path = Path(tmp_dir) / pkg_name / "__init__.py"
                    assert init_path.exists(), f"__init__.py not found in {pkg_name}"
            finally:
                os.chdir(original_cwd)

    def test_handles_existing_directories(self):
        """Test that the function handles existing directories gracefully."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Pre-create some directories
            Path(tmp_dir, "src").mkdir()
            Path(tmp_dir, "data").mkdir()
            Path(tmp_dir, "data", "raw").mkdir()
            
            original_cwd = os.getcwd()
            os.chdir(tmp_dir)
            
            try:
                # Should not raise an exception
                created = setup_directories()
                
                # All directories should still exist
                assert Path(tmp_dir, "src").exists()
                assert Path(tmp_dir, "data", "raw").exists()
            finally:
                os.chdir(original_cwd)