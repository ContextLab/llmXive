import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path
import sys

# Add the project code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'projects', 'PROJ-175-statistical-analysis-of-publicly-availab', 'code'))

from setup_directories import ensure_directories, verify_directories, log_setup_status, main

class TestSetupDirectories:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Create a temporary directory for each test and clean up afterwards."""
        self.temp_dir = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ensure_directories_creates_structure(self):
        """Test that ensure_directories creates the required folder structure."""
        base_path = self.temp_dir
        created = ensure_directories(base_path)
        
        assert len(created) > 0
        for path in created:
            assert os.path.isdir(path), f"Directory {path} was not created"
            
        # Check specific required directories exist
        expected_dirs = ["code", "data", "tests", "data/raw", "data/processed", "data/final", "data/logs", "docs"]
        for dir_name in expected_dirs:
            full_path = os.path.join(base_path, dir_name)
            assert os.path.isdir(full_path), f"Required directory {full_path} is missing"

    def test_verify_directories_success(self):
        """Test verify_directories when all directories exist."""
        base_path = self.temp_dir
        created = ensure_directories(base_path)
        
        verification = verify_directories(created)
        
        assert verification["all_passed"] is True
        assert len(verification["failed"]) == 0
        assert len(verification["verified"]) == len(created)

    def test_verify_directories_failure(self):
        """Test verify_directories when some directories are missing."""
        base_path = self.temp_dir
        # Create only one directory
        os.makedirs(os.path.join(base_path, "code"), exist_ok=True)
        
        # Try to verify a list that includes non-existent paths
        paths_to_verify = [
            os.path.join(base_path, "code"),
            os.path.join(base_path, "data"),  # Does not exist
            os.path.join(base_path, "tests")  # Does not exist
        ]
        
        verification = verify_directories(paths_to_verify)
        
        assert verification["all_passed"] is False
        assert len(verification["failed"]) == 2
        assert os.path.join(base_path, "code") in verification["verified"]

    def test_log_setup_status_creates_json(self):
        """Test that log_setup_status creates a valid JSON log file."""
        base_path = self.temp_dir
        os.makedirs(os.path.join(base_path, "data"), exist_ok=True)
        
        test_paths = [os.path.join(base_path, "code")]
        log_path = log_setup_status(base_path, "SUCCESS", test_paths)
        
        assert os.path.isfile(log_path)
        
        with open(log_path, "r") as f:
            log_data = json.load(f)
            
        assert "status" in log_data
        assert log_data["status"] == "SUCCESS"
        assert "timestamp" in log_data
        assert "paths_verified" in log_data
        assert log_data["paths_verified"] == test_paths

    def test_log_setup_status_failure(self):
        """Test log_setup_status with failed status."""
        base_path = self.temp_dir
        os.makedirs(os.path.join(base_path, "data"), exist_ok=True)
        
        test_paths = [os.path.join(base_path, "code")]
        failed_paths = [os.path.join(base_path, "data")]
        log_path = log_setup_status(base_path, "FAILED", test_paths, failed_paths)
        
        with open(log_path, "r") as f:
            log_data = json.load(f)
            
        assert log_data["status"] == "FAILED"
        assert "paths_failed" in log_data
        assert log_data["paths_failed"] == failed_paths