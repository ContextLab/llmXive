"""
Tests for the project initialization script (T001).
Verifies that the correct directory structure is created.
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest

# We need to temporarily add the code directory to the path to import setup_project
# In a real CI environment, this would be handled by the environment setup
import sys
from unittest.mock import patch

# Prepare the import path
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_project import initialize_project_structure


class TestProjectInitialization:
    """Test suite for initialize_project_structure function."""

    @pytest.fixture
    def temp_base_dir(self, tmp_path):
        """Create a temporary base directory for testing."""
        # We will run the function in a temp directory to avoid polluting the repo
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        yield tmp_path
        
        os.chdir(original_cwd)

    def test_creates_base_directory(self, temp_base_dir):
        """Test that the base project directory is created."""
        initialize_project_structure()
        
        base_path = temp_base_dir / "projects" / "PROJ-064-statistical-discrepancies-in-publicly-av"
        assert base_path.exists(), "Base project directory was not created"
        assert base_path.is_dir(), "Base project path is not a directory"

    def test_creates_code_directory(self, temp_base_dir):
        """Test that the code/ subdirectory is created."""
        initialize_project_structure()
        
        code_path = temp_base_dir / "projects" / "PROJ-064-statistical-discrepancies-in-publicly-av" / "code"
        assert code_path.exists(), "code/ directory was not created"
        assert code_path.is_dir(), "code/ path is not a directory"

    def test_creates_data_raw_directory(self, temp_base_dir):
        """Test that the data/raw/ subdirectory is created."""
        initialize_project_structure()
        
        data_raw_path = temp_base_dir / "projects" / "PROJ-064-statistical-discrepancies-in-publicly-av" / "data" / "raw"
        assert data_raw_path.exists(), "data/raw/ directory was not created"
        assert data_raw_path.is_dir(), "data/raw/ path is not a directory"

    def test_creates_data_processed_directory(self, temp_base_dir):
        """Test that the data/processed/ subdirectory is created."""
        initialize_project_structure()
        
        data_processed_path = temp_base_dir / "projects" / "PROJ-064-statistical-discrepancies-in-publicly-av" / "data" / "processed"
        assert data_processed_path.exists(), "data/processed/ directory was not created"
        assert data_processed_path.is_dir(), "data/processed/ path is not a directory"

    def test_creates_tests_directory(self, temp_base_dir):
        """Test that the tests/ subdirectory is created."""
        initialize_project_structure()
        
        tests_path = temp_base_dir / "projects" / "PROJ-064-statistical-discrepancies-in-publicly-av" / "tests"
        assert tests_path.exists(), "tests/ directory was not created"
        assert tests_path.is_dir(), "tests/ path is not a directory"

    def test_creates_docs_directory(self, temp_base_dir):
        """Test that the docs/ subdirectory is created."""
        initialize_project_structure()
        
        docs_path = temp_base_dir / "projects" / "PROJ-064-statistical-discrepancies-in-publicly-av" / "docs"
        assert docs_path.exists(), "docs/ directory was not created"
        assert docs_path.is_dir(), "docs/ path is not a directory"

    def test_creates_state_directory(self, temp_base_dir):
        """Test that the state/ subdirectory is created."""
        initialize_project_structure()
        
        state_path = temp_base_dir / "projects" / "PROJ-064-statistical-discrepancies-in-publicly-av" / "state"
        assert state_path.exists(), "state/ directory was not created"
        assert state_path.is_dir(), "state/ path is not a directory"

    def test_creates_config_directory(self, temp_base_dir):
        """Test that the config/ subdirectory is created."""
        initialize_project_structure()
        
        config_path = temp_base_dir / "projects" / "PROJ-064-statistical-discrepancies-in-publicly-av" / "config"
        assert config_path.exists(), "config/ directory was not created"
        assert config_path.is_dir(), "config/ path is not a directory"

    def test_all_directories_exist(self, temp_base_dir):
        """Test that all required directories are created in one go."""
        initialize_project_structure()
        
        base = temp_base_dir / "projects" / "PROJ-064-statistical-discrepancies-in-publicly-av"
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "tests",
            "docs",
            "state",
            "config"
        ]
        
        for dir_name in required_dirs:
            dir_path = base / dir_name
            assert dir_path.exists(), f"Required directory {dir_path} was not created"
            assert dir_path.is_dir(), f"Required path {dir_path} is not a directory"

    def test_idempotency(self, temp_base_dir):
        """Test that running the script twice does not cause errors."""
        # First run
        result1 = initialize_project_structure()
        assert result1 is True, "First run failed"
        
        # Second run
        result2 = initialize_project_structure()
        assert result2 is True, "Second run failed"
        
        # Verify structure still exists
        base = temp_base_dir / "projects" / "PROJ-064-statistical-discrepancies-in-publicly-av"
        assert base.exists(), "Base directory missing after second run"