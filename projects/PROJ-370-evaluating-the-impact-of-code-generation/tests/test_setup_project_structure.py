import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from code.setup_project_structure import create_directories, main

class TestSetupProjectStructure:
    def test_create_directories_creates_all_required(self):
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            
            # Call the function
            created_count = create_directories(base_path)
            
            # Verify count
            assert created_count == 7
            
            # Verify specific directories exist
            required_dirs = [
                "src",
                "data/raw",
                "data/derived",
                "data/annotations",
                "results",
                "tests",
                "specs"
            ]
            
            for dir_name in required_dirs:
                assert (base_path / dir_name).exists(), f"Directory {dir_name} was not created"

    def test_create_directories_skips_existing(self):
        """Test that existing directories are not recreated."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            
            # Pre-create one directory
            (base_path / "src").mkdir()
            
            # Call the function
            created_count = create_directories(base_path)
            
            # Should only create the remaining 6
            assert created_count == 6

    def test_main_function_returns_zero(self):
        """Test that main returns 0 on success."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch('code.setup_project_structure.create_directories', return_value=7):
                result = main()
                assert result == 0