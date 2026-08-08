"""
Unit test for Task T001g: Verify reports directory creation.
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest

# We import the functions directly to test them in isolation
# Note: In a real run, this would be run from the project root.
# For the test, we might need to adjust paths if running from a different cwd,
# but the logic assumes the script runs from the root.

# To make the test robust regardless of CWD, we will patch the working directory
# or test the logic by passing a specific path to a helper if we refactor.
# However, since the task is specifically about the 'reports' dir at root,
# we will simulate the environment.

from setup_reports_directory import create_reports_directory, verify_reports_directory


class TestT001gReports:
    
    @pytest.fixture(autouse=True)
    def setup_temp_dir(self, tmp_path):
        """Change to a temporary directory to avoid polluting the actual project root during tests."""
        # Save original cwd
        original_cwd = os.getcwd()
        # Change to temp dir
        os.chdir(tmp_path)
        yield tmp_path
        # Restore original cwd
        os.chdir(original_cwd)

    def test_create_reports_directory_creates_folder(self, setup_temp_dir):
        """Test that create_reports_directory actually creates the folder."""
        reports_path = create_reports_directory()
        assert reports_path.exists()
        assert reports_path.is_dir()
        assert reports_path.name == "reports"

    def test_create_reports_directory_idempotent(self, setup_temp_dir):
        """Test that calling create_reports_directory twice doesn't raise."""
        path1 = create_reports_directory()
        path2 = create_reports_directory()
        assert path1 == path2
        assert path1.exists()

    def test_verify_reports_directory_true(self, setup_temp_dir):
        """Test verification returns True for existing directory."""
        create_reports_directory()
        assert verify_reports_directory(Path("reports")) is True

    def test_verify_reports_directory_false_missing(self, setup_temp_dir):
        """Test verification returns False for missing directory."""
        # Ensure it doesn't exist
        if Path("reports").exists():
            shutil.rmtree("reports")
        
        assert verify_reports_directory(Path("reports")) is False

    def test_verify_reports_directory_false_file(self, setup_temp_dir):
        """Test verification returns False if 'reports' is a file, not a dir."""
        # Create a file named 'reports'
        Path("reports").touch()
        
        assert verify_reports_directory(Path("reports")) is False
        # Cleanup
        Path("reports").unlink()