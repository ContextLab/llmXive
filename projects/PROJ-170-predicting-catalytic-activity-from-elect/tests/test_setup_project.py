import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_project_root
from setup_project import create_directories, verify_directories, create_init_files

class TestDirectorySetup:
    """Tests for T001a: Create project directory structure."""

    def test_create_directories_creates_all_paths(self, tmp_path):
        """Verify that create_directories creates all required directories."""
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "outputs",
            "tests",
            "state/projects",
            "code/models"
        ]

        create_directories(tmp_path)

        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_verify_directories_passes_when_all_exist(self, tmp_path):
        """Verify that verify_directories returns True when all directories exist."""
        create_directories(tmp_path)
        
        # This should not raise an exception and should return True
        result = verify_directories(tmp_path)
        assert result is True

    def test_verify_directories_fails_when_missing(self, tmp_path):
        """Verify that verify_directories exits with error when a directory is missing."""
        # Create only some directories
        (tmp_path / "code").mkdir()
        
        # Mock sys.exit to capture the call
        with pytest.raises(SystemExit) as exc_info:
            verify_directories(tmp_path)
        
        assert exc_info.value.code == 1

    def test_create_init_files_creates_init_py(self, tmp_path):
        """Verify that create_init_files creates __init__.py in package directories."""
        package_dirs = ["code", "tests", "code/utils", "code/models"]
        
        create_directories(tmp_path)
        create_init_files(tmp_path)

        for dir_name in package_dirs:
            dir_path = tmp_path / dir_name
            init_file = dir_path / "__init__.py"
            assert init_file.exists(), f"__init__.py not created in {dir_path}"

    def test_full_setup_flow(self, tmp_path):
        """Test the complete setup flow: create dirs, init files, and verify."""
        # This mimics the main() function flow
        create_directories(tmp_path)
        create_init_files(tmp_path)
        
        # Should not raise
        verify_directories(tmp_path)