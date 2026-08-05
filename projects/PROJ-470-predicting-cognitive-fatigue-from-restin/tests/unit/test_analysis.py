import os
import sys
import json
import tempfile
import shutil
import pandas as pd
import pytest
import subprocess
from pathlib import Path

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from check_sample_size import check_sample_size, write_validation_report

class TestSampleSizeEnforcement:
    """Tests for T026a: N >= 30 constraint enforcement."""

    def setup_method(self):
        """Create temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, "data", "processed")
        self.analysis_dir = os.path.join(self.test_dir, "data", "analysis")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.analysis_dir, exist_ok=True)
        
        # Store original paths to restore later
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_sample_size_insufficient(self):
        """Test that script fails when N < 30."""
        # Create a mock LZC file with 29 participants
        lzc_path = os.path.join(self.data_dir, "lzc_metrics.csv")
        participants = [f"sub-{i:03d}" for i in range(29)]
        data = []
        for p in participants:
            for ch in ["Fz", "Cz", "Pz"]:
                data.append({"participant_id": p, "channel": ch, "lzc_value": 0.5})
        
        df = pd.DataFrame(data)
        df.to_csv(lzc_path, index=False)

        # Run check
        success, count, message = check_sample_size(
            metrics_file=lzc_path,
            alt_metrics_file=os.path.join(self.data_dir, "pe_metrics.csv"),
            min_n=30
        )

        assert success is False, "Should fail when N < 30"
        assert count == 29, f"Expected count 29, got {count}"
        assert "Insufficient sample size" in message, f"Expected error message, got: {message}"

    def test_sample_size_sufficient(self):
        """Test that script passes when N >= 30."""
        # Create a mock LZC file with 30 participants
        lzc_path = os.path.join(self.data_dir, "lzc_metrics.csv")
        participants = [f"sub-{i:03d}" for i in range(30)]
        data = []
        for p in participants:
            for ch in ["Fz", "Cz", "Pz"]:
                data.append({"participant_id": p, "channel": ch, "lzc_value": 0.5})
        
        df = pd.DataFrame(data)
        df.to_csv(lzc_path, index=False)

        # Run check
        success, count, message = check_sample_size(
            metrics_file=lzc_path,
            alt_metrics_file=os.path.join(self.data_dir, "pe_metrics.csv"),
            min_n=30
        )

        assert success is True, "Should pass when N >= 30"
        assert count == 30, f"Expected count 30, got {count}"
        assert "Sample size OK" in message, f"Expected success message, got: {message}"

    def test_sample_size_fallback_to_pe(self):
        """Test that script falls back to PE metrics if LZC is missing."""
        # Create PE file only
        pe_path = os.path.join(self.data_dir, "pe_metrics.csv")
        participants = [f"sub-{i:03d}" for i in range(30)]
        data = []
        for p in participants:
            for ch in ["Fz", "Cz", "Pz"]:
                data.append({"participant_id": p, "channel": ch, "pe_value": 0.8})
        
        df = pd.DataFrame(data)
        df.to_csv(pe_path, index=False)

        # Run check (LZC missing, should use PE)
        success, count, message = check_sample_size(
            metrics_file=os.path.join(self.data_dir, "lzc_metrics.csv"),
            alt_metrics_file=pe_path,
            min_n=30
        )

        assert success is True, "Should pass using PE fallback"
        assert count == 30, f"Expected count 30, got {count}"

    def test_sample_size_missing_files(self):
        """Test that script fails when no metrics files exist."""
        success, count, message = check_sample_size(
            metrics_file=os.path.join(self.data_dir, "lzc_metrics.csv"),
            alt_metrics_file=os.path.join(self.data_dir, "pe_metrics.csv"),
            min_n=30
        )

        assert success is False, "Should fail when no files exist"
        assert "not found" in message.lower()

    def test_validation_report_written(self):
        """Test that validation_report.json is written with correct schema."""
        # Create a mock file with N=29
        lzc_path = os.path.join(self.data_dir, "lzc_metrics.csv")
        participants = [f"sub-{i:03d}" for i in range(29)]
        data = [{"participant_id": p, "channel": "Fz", "lzc_value": 0.5} for p in participants]
        pd.DataFrame(data).to_csv(lzc_path, index=False)

        # Run check
        success, count, message = check_sample_size(
            metrics_file=lzc_path,
            alt_metrics_file=os.path.join(self.data_dir, "pe_metrics.csv"),
            min_n=30
        )

        # Verify report was written
        report_path = "data/analysis/validation_report.json"
        assert os.path.exists(report_path), "validation_report.json should be written"

        with open(report_path, 'r') as f:
            report = json.load(f)

        assert report["status"] == "FAIL"
        assert report["message"] == message
        assert "timestamp" in report
        assert report["details"]["participant_count"] == 29
        assert report["details"]["min_required"] == 30

    def test_script_exit_code_insufficient(self):
        """Test that the script exits with code 1 when N < 30."""
        # Create a mock file with N=29
        lzc_path = os.path.join(self.data_dir, "lzc_metrics.csv")
        participants = [f"sub-{i:03d}" for i in range(29)]
        data = [{"participant_id": p, "channel": "Fz", "lzc_value": 0.5} for p in participants]
        pd.DataFrame(data).to_csv(lzc_path, index=False)

        # Run the script as a subprocess
        result = subprocess.run(
            [sys.executable, "code/check_sample_size.py"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"
        assert "Insufficient sample size" in result.stderr or "Insufficient sample size" in result.stdout

    def test_script_exit_code_sufficient(self):
        """Test that the script exits with code 0 when N >= 30."""
        # Create a mock file with N=30
        lzc_path = os.path.join(self.data_dir, "lzc_metrics.csv")
        participants = [f"sub-{i:03d}" for i in range(30)]
        data = [{"participant_id": p, "channel": "Fz", "lzc_value": 0.5} for p in participants]
        pd.DataFrame(data).to_csv(lzc_path, index=False)

        # Run the script as a subprocess
        result = subprocess.run(
            [sys.executable, "code/check_sample_size.py"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
        assert "Sample size OK" in result.stderr or "Sample size OK" in result.stdout