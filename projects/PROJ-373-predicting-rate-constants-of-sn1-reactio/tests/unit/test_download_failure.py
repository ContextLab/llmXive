"""
Unit test for T600: Critical Review Concern (FR-009).
Verifies that code/data/download.py raises a fatal exception if the HuggingFace
dataset fetch fails, ensuring NO synthetic fallback or mock data generation occurs.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

import pytest

# Add project root to path to import config and data modules
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import DataConfig, ensure_dirs


class TestDownloadFailureIntegrity:
    """Tests to ensure download.py fails loudly without synthetic fallback."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Create a temporary directory structure for this test
        self.test_dir = tempfile.mkdtemp()
        self.data_raw_dir = Path(self.test_dir) / "data" / "raw"
        self.data_processed_dir = Path(self.test_dir) / "data" / "processed"
        
        self.data_raw_dir.mkdir(parents=True, exist_ok=True)
        self.data_processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Store original environment
        self.original_cwd = os.getcwd()
        self.original_data_raw = os.environ.get("DATA_RAW_DIR")
        self.original_data_processed = os.environ.get("DATA_PROCESSED_DIR")
        
        # Set environment variables to point to our temp dirs
        os.environ["DATA_RAW_DIR"] = str(self.data_raw_dir)
        os.environ["DATA_PROCESSED_DIR"] = str(self.data_processed_dir)
        
        # Change to temp directory to simulate project root
        os.chdir(self.test_dir)
        
        yield
        
        # Restore environment
        os.chdir(self.original_cwd)
        if self.original_data_raw is not None:
            os.environ["DATA_RAW_DIR"] = self.original_data_raw
        elif "DATA_RAW_DIR" in os.environ:
            del os.environ["DATA_RAW_DIR"]
            
        if self.original_data_processed is not None:
            os.environ["DATA_PROCESSED_DIR"] = self.original_data_processed
        elif "DATA_PROCESSED_DIR" in os.environ:
            del os.environ["DATA_PROCESSED_DIR"]
            
        # Cleanup temp directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_download_failure_raises_fatal_exception(self):
        """
        Test 1: Mock datasets.load_dataset to raise a ConnectionError.
        Assert that the script exits with code 1.
        """
        # Prepare the pipeline status as 'OK' to allow download to proceed
        pipeline_status_path = self.data_processed_dir / ".pipeline_status"
        pipeline_status_path.write_text("OK")

        # Mock the load_dataset function to raise an error
        with patch("datasets.load_dataset") as mock_load_dataset:
            mock_load_dataset.side_effect = ConnectionError("Network failure")
            
            # Run the download script
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "code" / "data" / "download.py")],
                capture_output=True,
                text=True,
                cwd=self.test_dir
            )
            
            # Assert exit code is 1 (failure)
            assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}. Stderr: {result.stderr}"
            
            # Assert that no synthetic or mock files were created in data/raw/
            raw_files = list(self.data_raw_dir.glob("*"))
            synthetic_files = [f for f in raw_files if f.name.startswith("synthetic_") or f.name.startswith("mock_")]
            assert len(synthetic_files) == 0, f"Synthetic/mock files found: {synthetic_files}"

    def test_download_failure_sets_aborted_status(self):
        """
        Test 2: Mock datasets.load_dataset to raise a ValueError (missing columns).
        Assert that data/processed/.pipeline_status is set to 'ABORTED'.
        """
        # Prepare the pipeline status as 'OK' to allow download to proceed
        pipeline_status_path = self.data_processed_dir / ".pipeline_status"
        pipeline_status_path.write_text("OK")

        # Mock the load_dataset function to raise a ValueError
        with patch("datasets.load_dataset") as mock_load_dataset:
            mock_load_dataset.side_effect = ValueError("Missing required columns in dataset")
            
            # Run the download script
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "code" / "data" / "download.py")],
                capture_output=True,
                text=True,
                cwd=self.test_dir
            )
            
            # Assert exit code is 1
            assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}. Stderr: {result.stderr}"
            
            # Assert that .pipeline_status is set to 'ABORTED'
            assert pipeline_status_path.exists(), "Pipeline status file was not created."
            status_content = pipeline_status_path.read_text().strip()
            assert status_content == "ABORTED", f"Expected 'ABORTED' in pipeline status, got '{status_content}'"

    def test_no_synthetic_fallback_on_failure(self):
        """
        Test 3: Verify that even if the script attempts to recover,
        it does NOT create synthetic/mock data files.
        """
        # Prepare the pipeline status as 'OK'
        pipeline_status_path = self.data_processed_dir / ".pipeline_status"
        pipeline_status_path.write_text("OK")

        # Mock the load_dataset function to fail
        with patch("datasets.load_dataset") as mock_load_dataset:
            mock_load_dataset.side_effect = Exception("Fetch failed")
            
            # Run the download script
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "code" / "data" / "download.py")],
                capture_output=True,
                text=True,
                cwd=self.test_dir
            )
            
            # Check for any file creation in data/raw/ that looks like synthetic data
            raw_files = list(self.data_raw_dir.glob("*"))
            for f in raw_files:
                assert not f.name.startswith("synthetic_"), f"Synthetic file created: {f.name}"
                assert not f.name.startswith("mock_"), f"Mock file created: {f.name}"
                assert not f.name.endswith(".fake"), f"Fake file created: {f.name}"

    def test_download_aborts_if_status_is_aborted(self):
        """
        Test 4: Verify that if .pipeline_status is already 'ABORTED',
        the script exits immediately with code 1 without attempting download.
        """
        # Set status to ABORTED
        pipeline_status_path = self.data_processed_dir / ".pipeline_status"
        pipeline_status_path.write_text("ABORTED")

        # Run the download script
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "code" / "data" / "download.py")],
            capture_output=True,
            text=True,
            cwd=self.test_dir
        )
        
        # Assert exit code is 1
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"
        
        # Assert no files were created in data/raw/
        raw_files = list(self.data_raw_dir.glob("*"))
        assert len(raw_files) == 0, f"Files created despite aborted status: {raw_files}"