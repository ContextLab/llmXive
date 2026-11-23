import pytest
import time
import subprocess
import sys
import os
import tempfile
import json
from pathlib import Path

class TestPerformanceVerification:
    """Test suite for performance verification task T039."""

    def test_cli_synthetic_execution_time(self):
        """Test that synthetic generation completes within time limit."""
        # Ensure data directory exists
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        
        cmd = [
            sys.executable,
            "code/src/cli.py",
            "--mode=synthetic",
            "--n=10000",
            "--seed=42"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Check return code
        assert result.returncode == 0, f"CLI failed with code {result.returncode}: {result.stderr}"
        
        # Check duration
        assert duration <= 600, f"Execution took {duration:.2f}s, exceeds 600s limit"
        
        # Check that output files were created
        assert Path("data/processed/results.json").exists(), "results.json not created"
        assert Path("data/processed/validated_fallback.csv").exists(), "validated_fallback.csv not created"
        assert Path("data/synthetic/mapping_log.json").exists(), "mapping_log.json not created"

    def test_perf_log_written(self):
        """Test that performance log is written correctly."""
        # Run the perf_monitor script directly
        cmd = [
            sys.executable,
            "code/src/perf_monitor.py"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        # Check return code
        assert result.returncode == 0, f"perf_monitor failed: {result.stderr}"
        
        # Check that perf_log.json exists
        assert Path("data/processed/perf_log.json").exists(), "perf_log.json not created"
        
        # Validate content
        with open("data/processed/perf_log.json", 'r') as f:
            log_data = json.load(f)
        
        assert "timestamp" in log_data, "Missing timestamp in log"
        assert "n_records" in log_data, "Missing n_records in log"
        assert "duration_seconds" in log_data, "Missing duration_seconds in log"
        assert log_data["n_records"] == 10000, "Incorrect n_records"
        assert log_data["duration_seconds"] <= 600, "Duration exceeds limit"

    def test_quickstart_performance(self):
        """Test performance as per quickstart.md requirements."""
        # This test verifies the specific command from T039
        cmd = [
            "time",
            sys.executable,
            "code/src/cli.py",
            "--mode=synthetic",
            "--n=10000"
        ]
        
        # Note: 'time' command behavior varies by shell, so we measure manually
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, "code/src/cli.py", "--mode=synthetic", "--n=10000"],
            capture_output=True,
            text=True,
            timeout=600
        )
        end_time = time.time()
        
        duration = end_time - start_time
        
        assert result.returncode == 0, f"Quickstart command failed: {result.stderr}"
        assert duration <= 600, f"Quickstart execution took {duration:.2f}s, exceeds 600s limit"
        
        # Verify output files
        assert Path("data/processed/results.json").exists()
        assert Path("data/processed/perf_log.json").exists()
        assert Path("data/processed/validated_fallback.csv").exists()
        assert Path("data/synthetic/mapping_log.json").exists()