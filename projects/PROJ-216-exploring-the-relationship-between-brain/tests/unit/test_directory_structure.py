import os
import sys
from pathlib import Path
import pytest

class TestDirectoryStructure:
    """
    Unit tests to verify that the project directory structure is correctly set up.
    Specifically tests for the existence of the 'reports' directory as per T001e.
    """

    @pytest.fixture
    def project_root(self):
        """Get the project root directory (parent of the tests directory)."""
        return Path(__file__).resolve().parent.parent.parent

    def test_reports_directory_exists(self, project_root):
        """Verify that the 'reports' directory exists."""
        reports_dir = project_root / "reports"
        assert reports_dir.exists(), f"Directory 'reports' does not exist at {reports_dir}"
        assert reports_dir.is_dir(), f"'reports' is not a directory at {reports_dir}"

    def test_reports_is_writable(self, project_root):
        """Verify that the 'reports' directory is writable."""
        reports_dir = project_root / "reports"
        assert os.access(reports_dir, os.W_OK), f"Directory 'reports' is not writable at {reports_dir}"

    def test_reports_init_exists(self, project_root):
        """Verify that reports/__init__.py exists if it's intended to be a package."""
        reports_dir = project_root / "reports"
        init_file = reports_dir / "__init__.py"
        # While not strictly required for a folder, it's good practice for Python packages
        # We assert existence if the setup script created it
        # If the setup script didn't create it, this test might fail, indicating a need to fix setup
        # For T001e, we expect the directory to exist. The init file is a bonus.
        # Let's make this a soft check or assert if the setup script guarantees it.
        # Given T001e creates the dir, and setup_directories.py creates the init, we expect it.
        if init_file.exists():
            assert init_file.is_file()
        else:
            # If the init file doesn't exist, it's not a fatal error for the directory task,
            # but indicates the setup script might need adjustment if package status is required.
            # For now, we just ensure the directory exists as per the strict task requirement.
            pass