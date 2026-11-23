"""
Tests for project structure initialization.

Verifies that the setup script creates the correct directory hierarchy
and that all required folders exist after execution.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.setup_project import create_structure, main
from code.config import get_project_root


class TestSetupProject:
    """Test suite for project structure creation."""

    def test_create_structure_returns_project_root(self):
        """Verify create_structure returns the correct project root path."""
        result = create_structure()
        expected = get_project_root()
        assert result == expected
        assert isinstance(result, Path)

    def test_data_directories_created(self):
        """Verify data/raw and data/processed directories are created."""
        project_root = get_project_root()
        create_structure()
        
        raw_dir = project_root / "data" / "raw"
        processed_dir = project_root / "data" / "processed"
        
        assert raw_dir.exists(), "data/raw directory should exist"
        assert raw_dir.is_dir(), "data/raw should be a directory"
        assert processed_dir.exists(), "data/processed directory should exist"
        assert processed_dir.is_dir(), "data/processed should be a directory"

    def test_code_subdirectories_created(self):
        """Verify all code subdirectories are created."""
        project_root = get_project_root()
        create_structure()
        
        code_subdirs = [
            "code/data",
            "code/tests",
            "code/utils",
            "code/models"
        ]
        
        for subdir in code_subdirs:
            full_path = project_root / subdir
            assert full_path.exists(), f"{subdir} directory should exist"
            assert full_path.is_dir(), f"{subdir} should be a directory"

    def test_docs_directory_created(self):
        """Verify docs directory is created."""
        project_root = get_project_root()
        create_structure()
        
        docs_dir = project_root / "docs"
        assert docs_dir.exists(), "docs directory should exist"
        assert docs_dir.is_dir(), "docs should be a directory"

    def test_init_files_created(self):
        """Verify __init__.py files are created for Python packages."""
        project_root = get_project_root()
        create_structure()
        
        init_files = [
            "code/__init__.py",
            "code/data/__init__.py",
            "code/tests/__init__.py",
            "code/utils/__init__.py",
            "code/models/__init__.py"
        ]
        
        for init_file in init_files:
            full_path = project_root / init_file
            assert full_path.exists(), f"{init_file} should exist"
            assert full_path.is_file(), f"{init_file} should be a file"

    def test_idempotent_creation(self):
        """Verify that running create_structure multiple times doesn't cause errors."""
        # Run twice
        result1 = create_structure()
        result2 = create_structure()
        
        # Both should succeed and return the same root
        assert result1 == result2
        assert result1 == get_project_root()

    def test_main_function_exit_code(self):
        """Verify main() returns 0 on successful execution."""
        # Mock print to avoid console noise
        with patch('builtins.print'):
            exit_code = main()
            assert exit_code == 0, "main() should return 0 on success"

    def test_directory_structure_completeness(self):
        """Verify the complete expected directory structure exists."""
        project_root = get_project_root()
        create_structure()
        
        expected_structure = {
            "data": ["raw", "processed"],
            "code": ["data", "tests", "utils", "models"],
            "docs": []
        }
        
        for parent, children in expected_structure.items():
            parent_path = project_root / parent
            assert parent_path.exists(), f"{parent} directory should exist"
            
            for child in children:
                child_path = parent_path / child
                assert child_path.exists(), f"{parent}/{child} should exist"
                assert child_path.is_dir(), f"{parent}/{child} should be a directory"

    def test_no_nested_data_in_code(self):
        """Verify data directories are siblings of code, not nested inside code."""
        project_root = get_project_root()
        create_structure()
        
        # data should be at root level
        data_root = project_root / "data"
        assert data_root.exists(), "data directory should be at project root"
        
        # code/data should exist but be different from data
        code_data = project_root / "code" / "data"
        assert code_data.exists(), "code/data should exist"
        assert code_data != data_root, "code/data and data should be different paths"

    def test_directory_permissions(self):
        """Verify created directories have write permissions."""
        project_root = get_project_root()
        create_structure()
        
        test_dir = project_root / "data" / "raw"
        assert os.access(test_dir, os.W_OK), "data/raw should be writable"
        
        test_dir = project_root / "code" / "tests"
        assert os.access(test_dir, os.W_OK), "code/tests should be writable"
