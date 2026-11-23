"""
Unit tests for the setup_directories module.
Verifies that directories and __init__.py files are created correctly.
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so we can import setup_directories
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_directories import create_directories


class TestSetupDirectories:
    """Tests for the setup_directories module."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to simulate the project root."""
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        yield Path(temp_dir)
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

    def test_directories_created(self, temp_project_root):
        """Test that all required directories are created."""
        create_directories()
        
        required_dirs = [
            "code",
            "code/data",
            "code/analysis",
            "code/audit",
            "code/utils",
            "data/raw",
            "data/processed",
            "tests/unit",
            "tests/integration",
            "reports/figures"
        ]
        
        for dir_path in required_dirs:
            full_path = temp_project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_init_files_created(self, temp_project_root):
        """Test that all required __init__.py files are created."""
        create_directories()
        
        required_init_files = [
            "code/__init__.py",
            "code/data/__init__.py",
            "code/analysis/__init__.py",
            "code/audit/__init__.py",
            "code/utils/__init__.py",
            "tests/unit/__init__.py",
            "tests/integration/__init__.py"
        ]
        
        for file_path in required_init_files:
            full_path = temp_project_root / file_path
            assert full_path.exists(), f"File {file_path} was not created"
            assert full_path.is_file(), f"{file_path} exists but is not a file"
            assert full_path.stat().st_size > 0, f"{file_path} is empty"

    def test_init_file_contents(self, temp_project_root):
        """Test that __init__.py files contain appropriate docstrings."""
        create_directories()
        
        expected_contents = {
            "code/__init__.py": "Root package for llmXive research code.",
            "code/data/__init__.py": "Data acquisition and processing module.",
            "code/analysis/__init__.py": "Analysis and statistical testing module.",
            "code/audit/__init__.py": "Audit and validation module.",
            "code/utils/__init__.py": "Utility functions and shared infrastructure.",
            "tests/unit/__init__.py": "Unit tests package.",
            "tests/integration/__init__.py": "Integration tests package."
        }
        
        for file_path, expected_text in expected_contents.items():
            full_path = temp_project_root / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert expected_text in content, f"Expected text '{expected_text}' not found in {file_path}"

    def test_idempotency(self, temp_project_root):
        """Test that running the script twice doesn't cause errors."""
        create_directories()
        # Run again - should not raise errors
        create_directories()
        
        # Verify directories still exist
        assert (temp_project_root / "code").exists()
        assert (temp_project_root / "code/data").exists()