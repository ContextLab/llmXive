"""
Test suite to verify the project directory structure.
"""
import pytest
from pathlib import Path
import sys
import os

# Add parent directory to path to allow imports if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.setup_directories import ensure_directory_exists

class TestDirectoryStructure:
    """Tests for directory structure verification."""

    def test_code_directory_exists(self):
        """Verify that the code/ directory exists."""
        base_path = Path(__file__).parent.parent
        code_dir = base_path.joinpath('code')
        assert code_dir.is_dir(), "The 'code/' directory must exist."

    def test_data_directory_exists(self):
        """Verify that the data/ directory exists."""
        base_path = Path(__file__).parent.parent
        data_dir = base_path.joinpath('data')
        assert data_dir.is_dir(), "The 'data/' directory must exist."

    def test_tests_directory_exists(self):
        """Verify that the tests/ directory exists."""
        base_path = Path(__file__).parent.parent
        tests_dir = base_path.joinpath('tests')
        assert tests_dir.is_dir(), "The 'tests/' directory must exist."

    def test_docs_directory_exists(self):
        """Verify that the docs/ directory exists."""
        base_path = Path(__file__).parent.parent
        docs_dir = base_path.joinpath('docs')
        assert docs_dir.is_dir(), "The 'docs/' directory must exist."

    def test_ensure_directory_creates_missing(self, tmp_path):
        """Test that ensure_directory_exists creates a missing directory."""
        test_dir = tmp_path / "new_dir"
        assert not test_dir.exists()
        
        result = ensure_directory_exists("new_dir", tmp_path)
        
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_directory_exists_already_present(self, tmp_path):
        """Test that ensure_directory_exists returns True for existing directory."""
        existing_dir = tmp_path / "existing_dir"
        existing_dir.mkdir()
        assert existing_dir.exists()
        
        result = ensure_directory_exists("existing_dir", tmp_path)
        
        assert result is True
        assert existing_dir.exists()