"""
Unit tests for T002: Data subdirectory creation and permissions.
"""

import os
import stat
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_subdirs import create_data_subdirectories, verify_directories


class TestDataSubdirectoryCreation:
    """Tests for data subdirectory creation functionality."""

    def setup_method(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_creates_raw_directory(self):
        """Test that data/raw/ directory is created."""
        results = create_data_subdirectories(Path(self.test_dir))
        raw_dir = Path(self.test_dir) / "data" / "raw"
        assert raw_dir.exists()
        assert raw_dir.is_dir()

    def test_creates_processed_directory(self):
        """Test that data/processed/ directory is created."""
        results = create_data_subdirectories(Path(self.test_dir))
        processed_dir = Path(self.test_dir) / "data" / "processed"
        assert processed_dir.exists()
        assert processed_dir.is_dir()

    def test_creates_logs_directory(self):
        """Test that data/logs/ directory is created."""
        results = create_data_subdirectories(Path(self.test_dir))
        logs_dir = Path(self.test_dir) / "data" / "logs"
        assert logs_dir.exists()
        assert logs_dir.is_dir()

    def test_sets_755_permissions(self):
        """Test that all directories have 755 permissions."""
        create_data_subdirectories(Path(self.test_dir))

        subdirs = ["raw", "processed", "logs"]
        for subdir_name in subdirs:
            subdir = Path(self.test_dir) / "data" / subdir_name
            mode = subdir.stat().st_mode & 0o777
            assert mode == 0o755, f"{subdir} has mode {oct(mode)}, expected 0o755"

    def test_755_permission_bits(self):
        """Test that 755 permissions grant correct read/write/execute bits."""
        create_data_subdirectories(Path(self.test_dir))

        subdir = Path(self.test_dir) / "data" / "raw"
        mode = subdir.stat().st_mode

        # Check owner: rwx (7)
        assert mode & stat.S_IRWXU == stat.S_IRWXU
        # Check group: r-x (5)
        assert mode & stat.S_IRGRP and mode & stat.S_IXGRP
        assert not (mode & stat.S_IWGRP)
        # Check others: r-x (5)
        assert mode & stat.S_IROTH and mode & stat.S_IXOTH
        assert not (mode & stat.S_IWOTH)

    def test_idempotent_creation(self):
        """Test that running creation twice doesn't cause errors."""
        create_data_subdirectories(Path(self.test_dir))
        results_second = create_data_subdirectories(Path(self.test_dir))

        # All should report "already existed"
        for _, was_created in results_second:
            assert not was_created, "Second run should not create new directories"

    def test_verify_directories_returns_correct_results(self):
        """Test that verify_directories correctly validates created directories."""
        create_data_subdirectories(Path(self.test_dir))
        verification = verify_directories(Path(self.test_dir))

        assert len(verification) == 3
        for path, expected_mode, is_valid in verification:
            assert is_valid, f"Directory {path} should be valid"
            assert expected_mode == 0o755

    def test_parent_data_directory_created(self):
        """Test that parent data/ directory is created if it doesn't exist."""
        results = create_data_subdirectories(Path(self.test_dir))
        data_dir = Path(self.test_dir) / "data"
        assert data_dir.exists()
        assert data_dir.is_dir()
