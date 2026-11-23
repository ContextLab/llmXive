import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project import create_directory_structure, write_setup_log

class TestSetupProject:
    """Tests for project initialization functionality."""

    def test_create_directory_structure(self, tmp_path):
        """Test that all required directories are created."""
        required_dirs = [
            "code", "data", "state", "tests", "docs",
            "data/raw", "data/processed", "tests/unit",
            "tests/integration", "state/projects", "tools", "reviews"
        ]
        
        result = create_directory_structure(str(tmp_path))
        
        assert result is True, "Directory creation should succeed"
        
        for dir_name in required_dirs:
            full_path = tmp_path / dir_name
            assert full_path.exists(), f"Directory {dir_name} should exist"
            assert full_path.is_dir(), f"{dir_name} should be a directory"

    def test_write_setup_log(self, tmp_path):
        """Test that setup log is written correctly."""
        create_directory_structure(str(tmp_path))
        log_path = write_setup_log(str(tmp_path), True)
        
        assert os.path.exists(log_path), "Setup log file should exist"
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "SUCCESS" in content, "Log should indicate success"
        assert "Timestamp" in content, "Log should contain timestamp"
        assert "code/" in content, "Log should list code directory"

    def test_write_setup_log_failure(self, tmp_path):
        """Test that setup log correctly reports failure."""
        log_path = write_setup_log(str(tmp_path), False)
        
        assert os.path.exists(log_path), "Setup log file should exist"
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "FAILED" in content, "Log should indicate failure"
        assert "NOT successfully" in content, "Log should indicate failure details"