"""
Tests for Task T001b: setup_data_directories.py
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
# We need to adjust the import path based on how tests are run.
# Assuming the test is run from the project root or code is in code/
import sys
from pathlib import Path

# Add the 'code' directory to the path if running from root
code_dir = Path(__file__).resolve().parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_data_directories import ensure_directory, main


class TestSetupDataDirectories:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Create a temporary directory structure for testing."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        
        # Change to the temp directory to simulate project root
        os.chdir(self.test_dir)
        
        # Create a dummy 'code' directory so the script finds its parent correctly
        (self.test_dir / "code").mkdir()
        
        yield
        
        # Cleanup
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_ensure_directory_creates_new(self):
        """Test that ensure_directory creates a new directory."""
        new_path = self.test_dir / "data" / "new_folder"
        assert not new_path.exists()
        
        ensure_directory(new_path)
        
        assert new_path.exists()
        assert new_path.is_dir()

    def test_ensure_directory_exists_no_error(self):
        """Test that ensure_directory does not error if dir exists."""
        existing_path = self.test_dir / "data" / "existing_folder"
        existing_path.mkdir(parents=True)
        
        # Should not raise
        ensure_directory(existing_path)
        
        assert existing_path.exists()

    def test_main_creates_structure(self):
        """Test that main() creates the required data directories."""
        # Run main
        main()
        
        # Verify structure
        data_root = self.test_dir / "data"
        assert data_root.exists()
        assert data_root.is_dir()
        
        required_dirs = [
            "stimuli",
            "processed",
            "measurements",
            "raw"
        ]
        
        for subdir in required_dirs:
            dir_path = data_root / subdir
            assert dir_path.exists(), f"Missing directory: {dir_path}"
            assert dir_path.is_dir(), f"Not a directory: {dir_path}"