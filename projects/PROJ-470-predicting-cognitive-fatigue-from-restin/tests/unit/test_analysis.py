import os
import sys
import json
import tempfile
import shutil
import pandas as pd
import pytest
from pathlib import Path

# Add the code directory to the path to allow imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from check_sample_size import check_sample_size, write_validation_report, load_config

class TestSampleSizeEnforcement:
    """Tests for T026a: Enforce N >= 30 constraint as a blocking gate."""

    def setup_method(self):
        """Create a temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data" / "processed"
        self.analysis_dir = Path(self.test_dir) / "data" / "analysis"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Save original working directory
        self.original_cwd = os.getcwd()
        # Change to test dir root to simulate project root
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up temporary directory and restore working directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_sample_size_insufficient_n29(self):
        """Test that the script exits with code 1 and writes validation_report.json when N=29."""
        # Create a mock lzc_metrics.csv with 29 participants
        lzc_path = self.data_dir / "lzc_metrics.csv"
        data = {
            "participant_id": [f"P{i:03d}" for i in range(1, 30)], # 29 participants
            "channel": ["Cz"] * 29,
            "lzc_value": [0.5 + i * 0.01 for i in range(29)]
        }
        df = pd.DataFrame(data)
        df.to_csv(lzc_path, index=False)

        # Run the check
        passed, message = check_sample_size()
        
        # Assertions
        assert passed is False, "Expected check_sample_size to return False for N=29"
        assert "Insufficient sample size" in message, f"Expected error message, got: {message}"
        
        # Verify validation_report.json was written
        report_path = self.analysis_dir / "validation_report.json"
        assert report_path.exists(), "validation_report.json was not created"
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report["status"] == "FAIL", f"Expected status 'FAIL', got: {report['status']}"
        assert report["details"]["n_found"] == 29, f"Expected n_found=29, got: {report['details']['n_found']}"
        assert report["details"]["n_required"] == 30, f"Expected n_required=30, got: {report['details']['n_required']}"

    def test_sample_size_sufficient_n30(self):
        """Test that the script passes when N=30."""
        # Create a mock lzc_metrics.csv with 30 participants
        lzc_path = self.data_dir / "lzc_metrics.csv"
        data = {
            "participant_id": [f"P{i:03d}" for i in range(1, 31)], # 30 participants
            "channel": ["Cz"] * 30,
            "lzc_value": [0.5 + i * 0.01 for i in range(30)]
        }
        df = pd.DataFrame(data)
        df.to_csv(lzc_path, index=False)

        # Run the check
        passed, message = check_sample_size()
        
        # Assertions
        assert passed is True, f"Expected check_sample_size to return True for N=30, got: {passed}"
        assert "passed" in message.lower(), f"Expected success message, got: {message}"
        
        # Verify validation_report.json was written
        report_path = self.analysis_dir / "validation_report.json"
        assert report_path.exists(), "validation_report.json was not created"
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report["status"] == "PASS", f"Expected status 'PASS', got: {report['status']}"
        assert report["details"]["n_found"] == 30, f"Expected n_found=30, got: {report['details']['n_found']}"

    def test_sample_size_missing_file(self):
        """Test that the script fails gracefully when metrics file is missing."""
        # Ensure no metrics file exists
        lzc_path = self.data_dir / "lzc_metrics.csv"
        pe_path = self.data_dir / "pe_metrics.csv"
        if lzc_path.exists(): lzc_path.unlink()
        if pe_path.exists(): pe_path.unlink()

        # Run the check
        passed, message = check_sample_size()
        
        # Assertions
        assert passed is False, "Expected check_sample_size to return False when file is missing"
        assert "Missing" in message or "missing" in message, f"Expected missing file error, got: {message}"

    def test_sample_size_falls_back_to_pe(self):
        """Test that the script uses pe_metrics.csv if lzc_metrics.csv is missing."""
        # Create only pe_metrics.csv with 30 participants
        lzc_path = self.data_dir / "lzc_metrics.csv"
        pe_path = self.data_dir / "pe_metrics.csv"
        if lzc_path.exists(): lzc_path.unlink()
        
        data = {
            "participant_id": [f"P{i:03d}" for i in range(1, 31)],
            "channel": ["Cz"] * 30,
            "pe_value": [0.6 + i * 0.01 for i in range(30)]
        }
        df = pd.DataFrame(data)
        df.to_csv(pe_path, index=False)

        # Run the check
        passed, message = check_sample_size()
        
        # Assertions
        assert passed is True, f"Expected check_sample_size to pass using PE file, got: {passed}"
        assert "passed" in message.lower()
