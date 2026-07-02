"""
Integration tests for logging in download and preprocess modules.

Verifies that setup_logger() is correctly used and logs are written
to the expected file (data/preprocess_log.txt).
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils import setup_logger
from download import verify_fMRI_availability
from preprocess import run_fmriprep, validate_preprocessed_outputs

class TestLoggingIntegration:
    """Tests to ensure logging is properly integrated."""

    @pytest.fixture(autouse=True)
    def setup_log_files(self, tmp_path):
        """Setup temporary directory structure for logging tests."""
        # Create required directories
        self.data_raw = tmp_path / "data" / "raw"
        self.data_raw.mkdir(parents=True, exist_ok=True)
        self.data_processed = tmp_path / "data" / "processed"
        self.data_processed.mkdir(parents=True, exist_ok=True)
        
        # Temporarily override global paths in modules
        # Note: In a real scenario, we might mock these or use config files
        # For this test, we rely on the fact that setup_logger writes to 
        # the default location, but we verify content by reading the file.
        # Since the modules use hardcoded paths relative to project root,
        # we run the test in a controlled environment.
        
        # Save original paths if needed, but here we just ensure directories exist
        # The actual logging file path is hardcoded in utils.py or the modules
        # We will verify that the log file is created and contains expected strings.
        
        # Create a dummy subject directory to test availability check
        self.test_subject_dir = self.data_raw / "100307"
        self.test_subject_dir.mkdir(parents=True, exist_ok=True)
        # Create a dummy NIfTI file to simulate PRESENT status
        (self.test_subject_dir / "MNINonLinear" / "Results" / "r11100").mkdir(parents=True, exist_ok=True)
        (self.test_subject_dir / "MNINonLinear" / "Results" / "r11100" / "rfMRI_REST1_LR.nii.gz").touch()

    def test_download_logs_availability_check(self, tmp_path):
        """Test that verify_fMRI_availability logs to preprocess_log.txt."""
        # We need to run this in the context where the log file is written
        # Since the path is relative, we change to the temp dir root to simulate project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Re-import to pick up the new CWD if paths are dynamic, 
            # but utils.py likely uses absolute paths or relative to script.
            # Assuming utils.py writes to data/preprocess_log.txt relative to cwd.
            
            # Run the function
            status = verify_fMRI_availability("100307")
            
            assert status['status'] == 'PRESENT'
            
            # Check if log file exists
            log_file = Path("data/preprocess_log.txt")
            assert log_file.exists(), "Log file was not created."
            
            content = log_file.read_text()
            assert "Checking fMRI availability" in content, "Log entry for availability check not found."
            assert "fMRI data found" in content, "Log entry for found data not found."
        finally:
            os.chdir(original_cwd)

    def test_download_logs_missing_data(self, tmp_path):
        """Test that verify_fMRI_availability logs warning for missing data."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Ensure data directory is empty for this subject
            (Path("data") / "raw" / "999999").mkdir(parents=True, exist_ok=True)
            
            status = verify_fMRI_availability("999999")
            
            assert status['status'] == 'MISSING'
            
            log_file = Path("data/preprocess_log.txt")
            assert log_file.exists()
            
            content = log_file.read_text()
            assert "MISSING" in content, "Log entry for missing data not found."
            assert "Data Gap" in content, "Reason for missing data not logged."
        finally:
            os.chdir(original_cwd)

    def test_preprocess_skips_missing_and_logs(self, tmp_path):
        """Test that run_fmriprep logs skip message when data is missing."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # No data created for this subject
            status = run_fmriprep("999999", mode="ci")
            
            assert status['success'] is False
            
            log_file = Path("data/preprocess_log.txt")
            assert log_file.exists()
            
            content = log_file.read_text()
            assert "Skipping preprocessing" in content, "Skip message not logged."
            assert "Data Unavailable" in content or "Data Gap" in content, "Reason for skip not logged."
        finally:
            os.chdir(original_cwd)