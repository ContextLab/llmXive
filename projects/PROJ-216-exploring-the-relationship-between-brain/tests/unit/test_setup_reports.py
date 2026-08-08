import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_reports_directory import create_reports_directory, verify_reports_directory

class TestSetupReportsDirectory:
    """
    Unit tests for the reports directory setup functionality.
    """

    def test_create_reports_directory_creates_folder(self, tmp_path):
        """
        Test that create_reports_directory actually creates the directory.
        """
        reports_path = create_reports_directory(str(tmp_path))
        
        assert reports_path.exists(), "The reports directory should exist after creation."
        assert reports_path.is_dir(), "The reports path should be a directory."
        assert reports_path.name == "reports", "The directory name should be 'reports'."

    def test_verify_reports_directory_returns_true(self, tmp_path):
        """
        Test that verify_reports_directory returns True when the directory exists.
        """
        create_reports_directory(str(tmp_path))
        assert verify_reports_directory(str(tmp_path)) is True

    def test_verify_reports_directory_returns_false_when_missing(self, tmp_path):
        """
        Test that verify_reports_directory returns False when the directory does not exist.
        """
        # Ensure the directory does not exist before testing
        reports_path = tmp_path / "reports"
        if reports_path.exists():
            reports_path.rmdir()
            
        assert verify_reports_directory(str(tmp_path)) is False

    def test_create_reports_directory_handles_existing(self, tmp_path):
        """
        Test that creating the directory when it already exists does not raise an error.
        """
        # Create it once
        path1 = create_reports_directory(str(tmp_path))
        # Create it again
        path2 = create_reports_directory(str(tmp_path))
        
        assert path1 == path2
        assert path1.exists()

    def test_directory_structure_compliance(self, tmp_path):
        """
        Test that the directory is created in the expected location relative to base.
        """
        base = tmp_path / "project_root"
        base.mkdir()
        
        result_path = create_reports_directory(str(base))
        expected_path = base / "reports"
        
        assert result_path == expected_path
        assert result_path.exists()
