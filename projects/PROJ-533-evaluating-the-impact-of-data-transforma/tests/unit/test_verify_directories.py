import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Add project root to path for imports
sys_path = Path(__file__).resolve().parent.parent.parent
if str(sys_path) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(sys_path))

from code.verify_directories import verify_directory, REQUIRED_DIRS


class TestVerifyDirectories:
    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Create a temporary directory structure simulating the project root."""
        # Create the required directories in the temp path
        for d in REQUIRED_DIRS:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)
        
        # Create a dummy file to simulate code/verify_directories.py location
        code_dir = tmp_path / "code"
        (code_dir / "verify_directories.py").touch()
        
        return tmp_path

    def test_verify_directory_exists(self, temp_project_root):
        """Test that verify_directory returns True for existing directories."""
        # Change working directory to the code folder so the script finds the root
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root / "code")
            for d in REQUIRED_DIRS:
                assert verify_directory(d) is True
        finally:
            os.chdir(original_cwd)

    def test_verify_directory_missing(self, temp_project_root):
        """Test that verify_directory returns False for missing directories."""
        # Remove one directory
        missing_dir = temp_project_root / REQUIRED_DIRS[0]
        shutil.rmtree(missing_dir)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root / "code")
            # The first directory should now be missing
            assert verify_directory(REQUIRED_DIRS[0]) is False
            # Others should still exist
            for d in REQUIRED_DIRS[1:]:
                assert verify_directory(d) is True
        finally:
            os.chdir(original_cwd)
