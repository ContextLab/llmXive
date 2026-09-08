"""
Tests for Task T009: Directory creation and verification.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_dirs import create_directories, verify_directories, REQUIRED_DIRS

class TestDirectorySetup:
    def setup_method(self):
        """Create a temporary directory to act as the project root for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up the temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_create_directories_creates_missing_dirs(self):
        """Test that create_directories creates directories that do not exist."""
        # Verify they don't exist yet
        for d in REQUIRED_DIRS:
            assert not (self.project_root / d).exists()

        success = create_directories(self.project_root)

        assert success is True
        for d in REQUIRED_DIRS:
            dir_path = self.project_root / d
            assert dir_path.exists()
            assert dir_path.is_dir()

    def test_create_directories_skips_existing_dirs(self):
        """Test that create_directories handles existing directories gracefully."""
        # Create one directory manually
        (self.project_root / REQUIRED_DIRS[0]).mkdir(parents=True, exist_ok=True)
        
        success = create_directories(self.project_root)
        
        assert success is True
        # All should exist
        for d in REQUIRED_DIRS:
            assert (self.project_root / d).exists()

    def test_verify_directories_returns_true_when_all_exist(self):
        """Test verify_directories when all directories are present."""
        # Create all directories
        for d in REQUIRED_DIRS:
            (self.project_root / d).mkdir(parents=True, exist_ok=True)
        
        result = verify_directories(self.project_root)
        assert result is True

    def test_verify_directories_returns_false_when_missing(self):
        """Test verify_directories when some directories are missing."""
        # Create only some
        (self.project_root / REQUIRED_DIRS[0]).mkdir(parents=True, exist_ok=True)
        
        result = verify_directories(self.project_root)
        assert result is False

    def test_verify_directories_fails_if_path_is_file(self):
        """Test verify_directories if a required path is a file, not a directory."""
        # Create a file where a directory should be
        file_path = self.project_root / REQUIRED_DIRS[0]
        file_path.touch()
        
        result = verify_directories(self.project_root)
        assert result is False