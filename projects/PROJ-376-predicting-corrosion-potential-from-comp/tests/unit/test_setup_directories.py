"""
Unit tests for the project directory structure setup (T001).
Verifies that all required directories exist after running the setup script.
"""
import os
import pytest
from pathlib import Path

# Import the setup function
from setup_directories import create_directories

@pytest.fixture(scope="module", autouse=True)
def setup_project_dirs():
    """Ensure directories are created before running tests."""
    create_directories()

class TestDirectoryStructure:
    """Test cases for verifying the project directory structure."""

    REQUIRED_DIRS = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "state",
        "contracts",
        "config",
        "code/data",
        "code/models",
        "code/utils",
        "code/tests",
    ]

    def test_all_required_directories_exist(self):
        """Verify that all required directories exist."""
        for dir_path in self.REQUIRED_DIRS:
            path = Path(dir_path)
            assert path.exists(), f"Directory {dir_path} does not exist"
            assert path.is_dir(), f"{dir_path} is not a directory"

    def test_code_directory_exists(self):
        """Verify code directory exists."""
        assert Path("code").exists()
        assert Path("code").is_dir()

    def test_data_directory_exists(self):
        """Verify data directory and its subdirectories exist."""
        assert Path("data").exists()
        assert Path("data/raw").exists()
        assert Path("data/processed").exists()
        assert Path("data/logs").exists()

    def test_state_directory_exists(self):
        """Verify state directory exists."""
        assert Path("state").exists()
        assert Path("state").is_dir()

    def test_contracts_directory_exists(self):
        """Verify contracts directory exists."""
        assert Path("contracts").exists()
        assert Path("contracts").is_dir()

    def test_config_directory_exists(self):
        """Verify config directory exists."""
        assert Path("config").exists()
        assert Path("config").is_dir()

    def test_code_subdirectories_exist(self):
        """Verify code subdirectories exist."""
        assert Path("code/data").exists()
        assert Path("code/models").exists()
        assert Path("code/utils").exists()
        assert Path("code/tests").exists()
