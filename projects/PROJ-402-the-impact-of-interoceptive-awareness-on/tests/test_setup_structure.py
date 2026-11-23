"""
Unit tests for the project structure setup script (T001).

These tests verify that the required directories and files are created correctly
when running code/setup_project_structure.py.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from setup_project_structure import create_directories, create_init_files, create_gitkeep_files

class TestProjectStructureSetup:
    """Test cases for project structure creation functions."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to act as the project root."""
        temp_dir = tempfile.mkdtemp(prefix="llmXive_test_")
        yield Path(temp_dir)
        # Cleanup after test
        shutil.rmtree(temp_dir)

    def test_create_directories(self, temp_project_root):
        """Test that create_directories creates the specified directories."""
        test_dirs = ['code', 'data', 'results', 'contracts']
        
        create_directories(temp_project_root, test_dirs)
        
        for dir_name in test_dirs:
            expected_path = temp_project_root / dir_name
            assert expected_path.exists(), f"Directory {expected_path} was not created"
            assert expected_path.is_dir(), f"{expected_path} is not a directory"

    def test_create_init_files(self, temp_project_root):
        """Test that create_init_files creates __init__.py in Python packages."""
        # First create the directories
        create_directories(temp_project_root, ['code', 'tests', 'code/utils'])
        
        # Then create init files
        create_init_files(temp_project_root, [])
        
        # Check that __init__.py files exist
        expected_inits = [
            temp_project_root / 'code' / '__init__.py',
            temp_project_root / 'tests' / '__init__.py',
            temp_project_root / 'code' / 'utils' / '__init__.py'
        ]
        
        for init_file in expected_inits:
            assert init_file.exists(), f"__init__.py not found at {init_file}"
            assert init_file.is_file(), f"{init_file} is not a file"

    def test_create_gitkeep_files(self, temp_project_root):
        """Test that create_gitkeep_files creates .gitkeep in data directories."""
        # First create the necessary directories
        create_directories(temp_project_root, [
            'data/raw', 'data/derived', 'results', 'figures', 'contracts', 'state/projects'
        ])
        
        # Then create gitkeep files
        create_gitkeep_files(temp_project_root, [])
        
        # Check that .gitkeep files exist
        expected_gitkeeps = [
            temp_project_root / 'data' / 'raw' / '.gitkeep',
            temp_project_root / 'data' / 'derived' / '.gitkeep',
            temp_project_root / 'results' / '.gitkeep',
            temp_project_root / 'figures' / '.gitkeep',
            temp_project_root / 'contracts' / '.gitkeep',
            temp_project_root / 'state' / 'projects' / '.gitkeep'
        ]
        
        for gitkeep_file in expected_gitkeeps:
            assert gitkeep_file.exists(), f".gitkeep not found at {gitkeep_file}"
            assert gitkeep_file.is_file(), f"{gitkeep_file} is not a file"

    def test_full_structure_creation(self, temp_project_root):
        """Test the full structure creation as it would happen in main()."""
        # Simulate the main function logic
        required_dirs = [
            'code', 'code/utils', 'code/tests', 'tests',
            'data', 'data/raw', 'data/derived',
            'results', 'contracts', 'state', 'state/projects',
            'specs', 'figures', 'docs'
        ]
        
        create_directories(temp_project_root, required_dirs)
        create_init_files(temp_project_root, required_dirs)
        create_gitkeep_files(temp_project_root, required_dirs)
        
        # Verify critical directories exist
        critical_dirs = [
            'code', 'tests', 'data', 'results', 
            'contracts', 'state/projects', 'specs', 'figures'
        ]
        
        for dir_name in critical_dirs:
            path = temp_project_root / dir_name
            assert path.exists(), f"Critical directory missing: {dir_name}"
            assert path.is_dir(), f"Critical path is not a directory: {dir_name}"

    def test_idempotency(self, temp_project_root):
        """Test that running the setup multiple times doesn't cause errors."""
        required_dirs = ['code', 'data', 'results']
        
        # Run twice
        create_directories(temp_project_root, required_dirs)
        create_directories(temp_project_root, required_dirs)
        
        # Verify directories still exist and are valid
        for dir_name in required_dirs:
            path = temp_project_root / dir_name
            assert path.exists()
            assert path.is_dir()
